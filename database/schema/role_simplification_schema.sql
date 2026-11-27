-- Professor decision, 2026-11-27. Apply only after 0007_guest_account_link.
-- Stop account writers first. Preserve IDs, historical roles and all references.
BEGIN;
SET LOCAL lock_timeout = '5s';
LOCK TABLE app_user, account_session, account_invitation, account_role_audit
    IN ACCESS EXCLUSIVE MODE;

DO $$
BEGIN
    -- Empty databases must remain installable before the first-admin bootstrap.
    IF EXISTS (SELECT 1 FROM app_user) AND NOT EXISTS (
        SELECT 1 FROM app_user
        WHERE role = 'admin' AND is_active AND password_hash IS NOT NULL
    ) THEN
        RAISE EXCEPTION 'Role simplification requires a usable administrator';
    END IF;
END;
$$;

-- Audit values are historical facts, not an authorization role catalogue.
ALTER TABLE account_role_audit
    ALTER COLUMN old_role TYPE TEXT USING old_role::text,
    ALTER COLUMN new_role TYPE TEXT USING new_role::text,
    ALTER COLUMN actor_user_id DROP NOT NULL,
    ADD COLUMN migration_reason TEXT,
    ADD CONSTRAINT account_role_audit_old_role_check
        CHECK (old_role IN ('candidate', 'academic_staff', 'interviewer', 'direction', 'admin')),
    ADD CONSTRAINT account_role_audit_new_role_check
        CHECK (new_role IN ('candidate', 'academic_staff', 'interviewer', 'direction', 'admin')),
    ADD CONSTRAINT account_role_audit_actor_check CHECK (
        (actor_user_id IS NOT NULL AND migration_reason IS NULL)
        OR (actor_user_id IS NULL AND migration_reason IS NOT NULL
            AND migration_reason = '0008_simplify_roles')
    );

CREATE TEMP TABLE obsolete_role_accounts ON COMMIT DROP AS
    SELECT id, role::text AS role, institution_id, is_active
    FROM app_user WHERE role IN ('academic_staff', 'direction');

INSERT INTO account_role_audit (
    actor_user_id, target_user_id, old_role, new_role,
    old_institution_id, new_institution_id, old_is_active, new_is_active,
    changed_at, migration_reason
)
SELECT NULL, id, role, 'interviewer', institution_id, NULL, is_active, false,
       now(), '0008_simplify_roles'
FROM obsolete_role_accounts;

UPDATE account_session SET revoked_at = now()
WHERE user_id IN (SELECT id FROM obsolete_role_accounts) AND revoked_at IS NULL;
UPDATE account_invitation SET revoked_at = now()
WHERE user_id IN (SELECT id FROM obsolete_role_accounts)
    AND used_at IS NULL AND revoked_at IS NULL;

-- Discover the generated constraint name instead of assuming PostgreSQL's name.
DO $$
DECLARE
    constraint_name TEXT;
    matches INTEGER := 0;
BEGIN
    FOR constraint_name IN
        SELECT conname FROM pg_constraint
        WHERE conrelid = 'app_user'::regclass AND contype = 'c'
            AND pg_get_constraintdef(oid) LIKE '%''academic_staff''%'
    LOOP
        matches := matches + 1;
        EXECUTE format('ALTER TABLE app_user DROP CONSTRAINT %I', constraint_name);
    END LOOP;
    IF matches <> 1 THEN
        RAISE EXCEPTION 'Expected one obsolete academic staff constraint, found %', matches;
    END IF;
END;
$$;

UPDATE app_user SET role = 'interviewer', is_active = false,
    institution_id = NULL, updated_at = now()
WHERE id IN (SELECT id FROM obsolete_role_accounts);

ALTER TABLE app_user ALTER COLUMN role DROP DEFAULT;
ALTER TYPE user_role RENAME TO user_role_retired_0008;
CREATE TYPE user_role AS ENUM ('candidate', 'interviewer', 'admin');
ALTER TABLE app_user ALTER COLUMN role TYPE user_role USING role::text::user_role;
ALTER TABLE app_user ALTER COLUMN role SET DEFAULT 'candidate'::user_role;
-- Unexpected dependencies fail the entire transaction; never use CASCADE here.
DROP TYPE user_role_retired_0008;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM app_user u JOIN obsolete_role_accounts o ON o.id = u.id
        WHERE u.role <> 'interviewer' OR u.is_active OR u.institution_id IS NOT NULL
    ) THEN
        RAISE EXCEPTION 'A migrated account retained unauthorized access';
    END IF;
END;
$$;
COMMIT;
