> **Superseded (kept as history).** This is the Module 3.1 diagram for the FeignException narrowing workflow, drawn before the roles and enforcement in the current policy existed. The current diagram is [`docs/orchestration-diagram.md`](../docs/orchestration-diagram.md).

                         +-------------------------+
                         | Orchestrator            |
                         +-----------+-------------+
                                     |
                    +----------------+----------------+
                    |                                 |
                    v                                 v
          +------------------+              +------------------+
          | Planner          |              | Implementer      |
          +------------------+              +------------------+
          | Receives:        |              | Receives:        |
          | Task brief +     |              | Plan + file list |
          | repo path        |              |                  |
          |                  |              | Returns:         |
          | Returns:         |              | Modified files + |
          | Plan + file list |              | change summary   |
          +---------+--------+              +---------+--------+
                    |                                 |
                    +----------------+----------------+
                                     |
                                     v
                         +-------------------------+
                         | Orchestrator             |
                         | Runs real ./mvnw test    |
                         | (stands in for Tester)   |
                         +-----------+-------------+
                                     |
                                     v
                         +-------------------------+
                         | Human                    |
                         | Approves or requests     |
                         | changes before commit    |
                         | (stands in for Reviewer) |
                         +-------------------------+
