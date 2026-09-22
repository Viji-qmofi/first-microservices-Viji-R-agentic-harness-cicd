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
