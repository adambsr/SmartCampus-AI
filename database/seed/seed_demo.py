"""SA-18: load demo data into the SmartCampus AI database.

Usage (from the repo root, with .env filled in):
    python database/seed/seed_demo.py --db test     # smartcampus_test
    python database/seed/seed_demo.py --db main     # neondb (the demo database)

It EMPTIES all 18 tables first, then loads:
- IIT and ISB, the 31 real programs from catalog_inventory.csv (iit.tn / isb.tn),
  their admission rules, accepted backgrounds, published fees and IIT fee rules,
- pathways between programs, one open admission campaign per school,
- 5 staff accounts and 5 candidates whose applications sit at different statuses,
- 5 official source documents and one sync job.

Fees are copied from the websites and stay is_confirmed = false until the admissions
office confirms what "/9 mois" means. People and emails are fake (example.com).
"""
import argparse
import csv
import os
from pathlib import Path

import psycopg
from dotenv import find_dotenv, load_dotenv

HERE = Path(__file__).resolve().parent
YEAR = "2026-2027"

TABLES = [
    "application_document", "sync_job", "document_chunk", "source_document",
    "recommendation", "application_history", "application", "candidate_profile", "app_user",
    "admission_campaign", "pathway", "fee_rule", "tariff", "accepted_background",
    "admission_requirement", "specialization", "program", "institution",
]

# Licence specialties accepted by each IIT engineering program
# (source: IIT "Critères d'admission", DC-SC-17, 17/06/2025)
CRITERIA_PDF = "https://iit.tn/wp-content/uploads/2026/10/Criteres_d_admission.pdf"
ENGINEERING_LICENCES = {
    "IIT-ING-GC": ["Génie civil", "Construction", "Construction métallique",
                   "Planification et gestion des travaux", "Infrastructures", "Travaux publics",
                   "Ponts et routes", "Gestion des chantiers"],
    "IIT-ING-GIND": ["Maintenance industrielle", "Maîtrise et gestion de la qualité",
                     "Gestion des systèmes industriels", "Optimisation et recherche opérationnelle",
                     "Logistique industrielle", "Mathématiques et informatique", "Mathématiques",
                     "Industries des plastiques", "Mathématiques appliquées",
                     "Conception et fabrication mécaniques", "Physique et chimie",
                     "Mécanique et informatique industrielle", "Physique", "Énergie et environnement",
                     "Logistique des opérations internationales", "Logistique de la distribution"],
    "IIT-ING-GM": ["Maintenance industrielle", "Électromécanique",
                   "Conception et fabrication mécaniques", "Conception et production intégrées",
                   "Construction mécanique et fabrication", "Industrie des plastiques", "Mécatronique",
                   "Construction métallique", "Sciences et ingénierie des matériaux",
                   "Hydroélectromécanique", "Structures métalliques et forge", "Énergie",
                   "Entretien automobile", "Mécanique industrielle"],
    "IIT-ING-GP": ["Génie des procédés industriels", "Génie chimique", "Procédés biotechnologiques",
                   "Chimie industrielle", "Génie des procédés chimiques",
                   "Génie des procédés alimentaires"],
    "IIT-ING-GI": ["Sciences de l'information", "Ingénierie des systèmes d'information",
                   "Technologies de l'information", "Automatisation et informatique industrielle",
                   "Systèmes automatisés et réseaux industriels", "Ingénierie de l'information",
                   "Informatique de gestion", "Mathématiques", "Mathématiques appliquées",
                   "Sciences et technologies de l'information et de la communication",
                   "Électronique et électrotechnique", "Informatique de précision et appareils mobiles",
                   "Informatique et multimédia", "Ingénierie logicielle et systèmes d'information",
                   "Ingénierie des réseaux et des systèmes", "Systèmes mobiles et Internet des objets",
                   "Développement des systèmes d'information", "Systèmes portables et mobiles",
                   "Réseaux et services informatiques", "Multimédia et développement web",
                   "Intelligence d'affaires", "Services électroniques dans le monde des affaires",
                   "Systèmes d'information dans le monde des affaires", "Mathématiques et informatique"],
}

FEES_PAGE = "https://iit.tn/test/procedure-et-frais-dinscription/"
IIT_FEE_RULES = [
    ("Réduction de 5 % si la totalité des frais de scolarité est payée dès l'inscription.", 5),
    ("Les tarifs des nouveaux étudiants sont majorés de 5 % par rapport à l'année précédente "
     "(sauf Architecture, stables de la 4e à la 6e année).", 5),
    ("Toute inscription est ferme et définitive: aucun remboursement en cas d'abandon.", None),
    ("Les étudiants internationaux paient au taux de change enregistré le 01/10 de l'année en cours.", None),
]

# (from, to, condition). IIT routes follow the admission criteria; ISB routes are demo examples.
PATHWAYS = [
    *[("IIT-PREPA", eng, "Diplôme du cycle préparatoire (MP/PC/PT), puis dossier, entretien et test")
      for eng in ("IIT-ING-GI", "IIT-ING-GC", "IIT-ING-GIND", "IIT-ING-GM", "IIT-ING-GP")],
    *[(lic, "IIT-ING-GI", "Licence dans une spécialité acceptée, puis dossier, entretien et test")
      for lic in ("IIT-LIC-GLSI", "IIT-LIC-RC", "IIT-LIC-IOT", "IIT-LIC-BD")],
    ("IIT-LIC-MECA", "IIT-ING-GM", "Licence en mécatronique, puis dossier, entretien et test"),
    ("IIT-LIC-MSI", "IIT-ING-GIND", "Licence en gestion des systèmes industriels, puis dossier, entretien et test"),
    ("IIT-LIC-GLSI", "IIT-MAST", "Licence (exemple de démonstration)"),
    ("ISB-LBA", "ISB-MBA", "Licence, entretien de sélection (exemple de démonstration)"),
    ("ISB-LN-FIN", "ISB-MP-FEIF", "Licence (exemple de démonstration)"),
    ("ISB-LN-COMPTA", "ISB-MP-FEIF", "Licence (exemple de démonstration)"),
]

STAFF = [
    ("admin@example.com", "Admin Plateforme", "admin", None),
    ("academique.iit@example.com", "Responsable académique IIT", "academic_staff", "IIT"),
    ("academique.isb@example.com", "Responsable académique ISB", "academic_staff", "ISB"),
    ("entretien@example.com", "Responsable entretien", "interviewer", None),
    ("direction@example.com", "Direction", "direction", None),
]

# email, name, profile, program code, status path, recommendation (program, score, justification)
CANDIDATES = [
    ("yassine.demo@example.com", "Yassine Ben Salah",
     dict(current_level="Bac", bac_section="Math", bac_year=2026, bac_average=14.25,
          favorite_subjects=["Mathématiques", "Informatique"], interests=["développement web", "IA"],
          career_goal="Ingénieur logiciel", preferred_language="tn"),
     "IIT-LIC-GLSI", ["draft"],
     ("IIT-LIC-GLSI", 86, "Bac Math accepté, intérêt fort pour le développement logiciel.")),
    ("amira.demo@example.com", "Amira Trabelsi",
     dict(current_level="Bac", bac_section="Sciences", bac_year=2026, bac_average=15.10,
          favorite_subjects=["Physique", "Mathématiques"], interests=["robotique"],
          career_goal="Ingénieure en mécanique", preferred_language="fr"),
     "IIT-PREPA", ["draft", "submitted"],
     ("IIT-PREPA", 81, "Profil scientifique solide; la prépa ouvre ensuite le génie mécanique.")),
    ("mehdi.demo@example.com", "Mehdi Kammoun",
     dict(current_level="Licence 3", last_diploma="Licence", bac_section="Informatique",
          last_diploma_specialty="Ingénierie logicielle et systèmes d'information",
          interests=["cybersécurité", "cloud"], career_goal="Architecte logiciel",
          preferred_language="arabizi"),
     "IIT-ING-GI", ["draft", "submitted", "qcm_pending"],
     ("IIT-ING-GI", 90, "Sa licence figure dans la liste des spécialités acceptées en Génie Informatique.")),
    ("sarra.demo@example.com", "Sarra Jlassi",
     dict(current_level="Bac", bac_section="Economie et Gestion", bac_year=2026, bac_average=13.40,
          favorite_subjects=["Anglais", "Gestion"], interests=["management international"],
          career_goal="Manager", preferred_language="fr"),
     "ISB-LBA", ["draft", "submitted", "qcm_pending", "interview_scheduled"],
     ("ISB-LBA", 78, "Bon niveau d'anglais; programme entièrement enseigné en anglais.")),
    ("karim.demo@example.com", "Karim Gargouri",
     dict(current_level="Bac", bac_section="Technique", bac_year=2025, bac_average=12.80,
          favorite_subjects=["Électricité"], interests=["énergies renouvelables"],
          career_goal="Technicien supérieur en énergie", preferred_language="tn"),
     "IIT-LIC-SEER", ["draft", "submitted", "qcm_pending", "interview_scheduled", "accepted", "enrolled"],
     ("IIT-LIC-SEER", 84, "Bac Technique accepté; projet professionnel aligné sur les énergies renouvelables.")),
]

DOCUMENTS = [
    ("iit-cb74cdfb72fa", "IIT", None, "Critères d'admission", "registration", "pdf", CRITERIA_PDF,
     "Pour être admis, le candidat doit avoir un diplôme de préparatoire (MP/PC/PT) ou une licence "
     "dans l'une des spécialités listées pour chaque filière d'ingénierie."),
    ("iit-5cc6c686ac54", "IIT", None, "Procédure et frais d'inscription", "tuition_fees", "html", FEES_PAGE,
     "Pour les cinq filières d'ingénierie, l'admission est effectuée par concours sur dossier suivie "
     "d'un entretien de validation et d'un test d'admission."),
    ("iit-a1230b982ad5", "IIT", "IIT-ING-GI", "Génie Informatique", "academic_program", "html",
     "https://iit.tn/filieres-ingenieur/genie-informatique/",
     "Compétences visées: administration des systèmes et des réseaux, conception des systèmes "
     "informatiques, développement informatique."),
    ("isb-32c90833ca09", "ISB", "ISB-MBA", "MBA en Tunisie", "academic_program", "html",
     "https://isb.tn/program-mba/",
     "Prérequis: Licence. Durée: 2 ans. Langue: Anglais. 120 crédits. Date limite d'inscription: 01 octobre."),
    ("isb-93e3c01dafec", "ISB", None, "Pré-inscription ISB", "registration", "html",
     "https://isb.tn/pre-inscription/",
     "Une fois votre demande d'admission transmise à l'ISB, elle sera étudiée par une commission pédagogique."),
]


def split(value):
    return [v.strip() for v in value.split("|") if v.strip()] if value else []


def backgrounds(code, raw):
    """Turn the CSV's accepted_backgrounds into (kind, value) rows.

    'BAC Math|Sciences|...' -> every item is a bac section.
    'Prepa MP' -> prepa track; 'Prepa (toutes)' -> MP, PC and PT.
    'Licence (liste ...)' -> the licence specialties from the criteria PDF.
    Items like 'Bac (section non precisee)' carry no list and stay in the notes.
    """
    items = split(raw)
    if items and items[0].upper().startswith("BAC ") and "(" not in items[0]:
        rows = [("bac_section", items[0][4:].strip())] + [("bac_section", i) for i in items[1:]]
    else:
        rows = []
        for item in items:
            if item == "Prepa (toutes)":
                rows += [("prepa_track", t) for t in ("MP", "PC", "PT")]
            elif item.startswith("Prepa "):
                rows.append(("prepa_track", item[6:].strip()))
            elif "(" not in item:
                rows.append(("diploma", item))
    rows += [("licence_specialty", s) for s in ENGINEERING_LICENCES.get(code, [])]
    return rows


def seed(conn):
    cur = conn.cursor()
    cur.execute("TRUNCATE " + ", ".join(TABLES) + " RESTART IDENTITY CASCADE")

    inst = {}
    for code, name, site in [("IIT", "Institut International de Technologie", "https://iit.tn"),
                             ("ISB", "International School of Business", "https://isb.tn")]:
        cur.execute("INSERT INTO institution (code, name, city, website) VALUES (%s, %s, 'Sfax', %s) RETURNING id",
                    (code, name, site))
        inst[code] = cur.fetchone()[0]

    prog = {}
    with open(HERE / "catalog_inventory.csv", encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            cur.execute(
                """INSERT INTO program (institution_id, code, name, level, program_type, field,
                       duration_years, teaching_language, labels, source_url)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                (inst[r["institution"]], r["code"], r["name"], r["level"], r["program_type"] or None,
                 r["field"] or None, int(r["duration_years"]) if r["duration_years"] else None,
                 r["teaching_language"] or "fr",
                 (["EURO-INF"] if r["code"] == "IIT-ING-GI" else ["EUR-ACE"] if r["code"] == "IIT-ING-GIND" else None),
                 r["source_url"]))
            pid = prog[r["code"]] = cur.fetchone()[0]

            cur.execute(
                """INSERT INTO admission_requirement (program_id, entry_level, selection_steps, notes, source_url)
                   VALUES (%s, %s, %s, %s, %s) RETURNING id""",
                (pid, r["entry_level"], split(r["selection_steps"]) or None, r["notes"] or None,
                 CRITERIA_PDF if r["code"] in ENGINEERING_LICENCES else r["source_url"]))
            req_id = cur.fetchone()[0]
            for kind, value in backgrounds(r["code"], r["accepted_backgrounds"]):
                cur.execute("""INSERT INTO accepted_background (requirement_id, kind, value)
                               VALUES (%s, %s, %s) ON CONFLICT DO NOTHING""", (req_id, kind, value))

            period = r["fee_period"]
            for category, amount, currency in [("national", r["fee_national_tnd"], "TND"),
                                               ("international", r["fee_international_eur"], "EUR")]:
                if amount:
                    cur.execute(
                        """INSERT INTO tariff (program_id, academic_year, student_category, amount, currency,
                               period, installments, is_confirmed, notes, source_url)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, false, %s, %s)""",
                        (pid, YEAR, category, amount, currency,
                         "year" if period == "year" else "month",
                         None if period == "year" else 9,
                         "Montant affiché sur le site" + ("" if period == "year" else " ('/9 mois', à confirmer)"),
                         r["source_url"]))

    for rule, pct in IIT_FEE_RULES:
        cur.execute("INSERT INTO fee_rule (institution_id, rule, percent, source_url) VALUES (%s, %s, %s, %s)",
                    (inst["IIT"], rule, pct, FEES_PAGE))
    for src, dst, cond in PATHWAYS:
        cur.execute("INSERT INTO pathway (from_program_id, to_program_id, condition) VALUES (%s, %s, %s)",
                    (prog[src], prog[dst], cond))
    camp = {}
    for code in ("IIT", "ISB"):
        cur.execute("""INSERT INTO admission_campaign (institution_id, academic_year, opens_at, closes_at, status)
                       VALUES (%s, %s, '2026-03-01', '2026-10-01', 'open') RETURNING id""", (inst[code], YEAR))
        camp[code] = cur.fetchone()[0]

    users = {}
    for email, name, role, school in STAFF:
        cur.execute("""INSERT INTO app_user (email, full_name, role, institution_id)
                       VALUES (%s, %s, %s, %s) RETURNING id""", (email, name, role, inst.get(school)))
        users[email] = cur.fetchone()[0]
    reviewer = users["academique.iit@example.com"]

    for email, name, profile, code, path, (rec_code, score, why) in CANDIDATES:
        cur.execute("INSERT INTO app_user (email, full_name) VALUES (%s, %s) RETURNING id", (email, name))
        uid = cur.fetchone()[0]
        cols = ", ".join(profile)
        cur.execute(f"INSERT INTO candidate_profile (user_id, {cols}) VALUES (%s, {', '.join(['%s'] * len(profile))})",
                    (uid, *profile.values()))
        # short paths are still waiting for staff review; longer ones were confirmed
        if len(path) <= 2:
            rec_status, rec_by, rec_at = "proposed", None, None
        else:
            rec_status, rec_by, rec_at = "confirmed", reviewer, "2026-11-01"
        cur.execute("""INSERT INTO recommendation (user_id, program_id, score, rank, justification, status,
                           reviewed_by, reviewed_at)
                       VALUES (%s, %s, %s, 1, %s, %s, %s, %s)""",
                    (uid, prog[rec_code], score, why, rec_status, rec_by, rec_at))
        school = code.split("-")[0]
        cur.execute("SELECT set_config('app.user_id', %s, true)", (str(uid),))  # the candidate creates it
        cur.execute("""INSERT INTO application (user_id, program_id, campaign_id) VALUES (%s, %s, %s) RETURNING id""",
                    (uid, prog[code], camp[school]))
        app_id = cur.fetchone()[0]
        for status in path[1:]:
            # the trigger writes application_history for every step
            # the candidate submits; staff make every later move
            actor = uid if status == "submitted" else reviewer
            cur.execute("SELECT set_config('app.user_id', %s, true)", (str(actor),))
            cur.execute("""UPDATE application SET status = %s, consent_at = COALESCE(consent_at, now()),
                               submitted_at = COALESCE(submitted_at, now()), updated_at = now()
                           WHERE id = %s""", (status, app_id))

    for ext, school, pcode, title, dtype, fmt, url, content in DOCUMENTS:
        cur.execute("""INSERT INTO source_document (external_id, institution_id, program_id, title, document_type,
                           format, source_url, language, content, crawled_at)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, 'fr', %s, '2026-11-18') RETURNING id""",
                    (ext, inst[school], prog.get(pcode), title, dtype, fmt, url, content))
        doc_id = cur.fetchone()[0]
        cur.execute("""INSERT INTO document_chunk (document_id, chunk_index, heading_path, content)
                       VALUES (%s, 0, %s, %s)""", (doc_id, title, content))
    cur.execute("""INSERT INTO sync_job (started_at, finished_at, status, documents_seen, added)
                   VALUES ('2026-11-18 22:50', '2026-11-18 23:05', 'success', %s, %s)""",
                (len(DOCUMENTS), len(DOCUMENTS)))


def main():
    ap = argparse.ArgumentParser(description="Load SmartCampus AI demo data (empties the tables first).")
    ap.add_argument("--db", choices=["test", "main"], required=True,
                    help="test = TEST_DATABASE_URL, main = DATABASE_URL")
    args = ap.parse_args()
    load_dotenv(find_dotenv(usecwd=True))
    url = os.environ["TEST_DATABASE_URL" if args.db == "test" else "DATABASE_URL"]
    with psycopg.connect(url) as conn:
        seed(conn)
        conn.commit()
        for t in reversed(TABLES):
            n = conn.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
            print(f"{t:24} {n}")


if __name__ == "__main__":
    main()
