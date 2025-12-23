# API Tooling Recommendation

Due to the security issues in Postman, alternative API tooling options have been reviewed. This document
compares several tools to help identify suitable replacements based on usability, security, and collaboration
needs.

| API Tooling | Pros | Cons |
|-------------|------|------|
| **Curl** | Commands easily found online; straightforward for basic REST testing via command line; free | No official documentation; lacks advanced features like mocking APIs; no independent UI (terminal only) |
| [**REST Client Extension**](https://marketplace.visualstudio.com/items?itemName=humao.rest-client) | Easy to install and use within VS Code; supports many key features; good [documentation](https://github.com/Huachao/vscode-restclient/blob/master/README.md); no login or cloud sync needed; free | Limited to VS Code IDE; no independent UI; collaboration is harder |
| [**Insomnia**](https://docs.insomnia.rest/insomnia/get-started) | Advanced capabilities; supports REST, GraphQL, and WebSockets; local and [cloud](https://docs.insomnia.rest/insomnia/scratchpad) modes; independent UI; many plugins | Some features rely on cloud sync; premium tier needed for full feature set; AI features may be problematic for sensitive data; heavier resource usage |
| [**Bruno**](https://docs.usebruno.com/send-requests/REST/rest-api) | Offline-first tool; no login needed; easy import from other tools via [translator](https://docs.usebruno.com/get-started/import-export-data/script-translator); great documentation; Git-friendly | Some premium features; no WebSocket support; no cloud sync makes collaboration harder; limited for heavy API workflows |

## Outcome

Alternative tools besides Postman were investigated due to potential security risks related to cloud syncing.
Each of the above tools is suitable depending on specific development and compliance requirements.

While Insomnia is a strong candidate with rich functionality, its AI features and cloud reliance may raise
concerns when working with sensitive data. REST Client Extension and Bruno both offer local testing with no
cloud sync and could be better suited for secure environments.

This document is not a directive but a resource to capture the evaluation process and summarize the pros and
cons of viable Postman alternatives.
