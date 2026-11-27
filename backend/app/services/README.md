# Business services

Application and business logic live here. Endpoint modules handle HTTP concerns
and call services; settings belong in `app.core`. Implemented services include
catalog and admissions access, SA-25 visitor sessions, SA-26 conversations, and
SA-28 account authentication, roles, candidate reads, and staff account
management. SA-29 adds consented visitor-session conversation linking and
candidate conversation history. The conversation APIs store messages; assistant
response generation is not implemented.
