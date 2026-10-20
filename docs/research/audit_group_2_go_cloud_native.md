# Audit Group 2: Go & Cloud-Native MCPs

## Category Breakdown Summary
| Issue Type | Count |
| --- | --- |
| `MISSING_REGISTRY_INDEXER_PKG_GO_DEV` | 157 |
| `AST_UNSUPPORTED_SDK_MACRO` | 2 |
| `BINARY_CONTAINER_ONLY` | 5 |
| `MONOREPO_NESTED_PATH` | 1 |
| **Present in Repo** | 35 |

## Detailed Audit Results
| MCP Name | Location | Present in Repo? | Issue Type | Specific Technical Remedy |
| --- | --- | --- | --- | --- |
| github-mcp-server | https://github.com/github/github-mcp-server | Yes |  |  |
| whatsapp-mcp | https://github.com/lharries/whatsapp-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-toolbox | https://github.com/googleapis/mcp-toolbox | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-grafana | https://github.com/grafana/mcp-grafana | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| kubernetes-mcp-server | https://github.com/containers/kubernetes-mcp-server | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| slack-mcp-server | https://github.com/korotovsky/slack-mcp-server | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp | https://github.com/neo4j/mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| terraform-mcp-server | https://github.com/hashicorp/terraform-mcp-server | Yes |  |  |
| matlab-mcp-server | https://github.com/matlab/matlab-mcp-server | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-language-server | https://github.com/isaacphi/mcp-language-server | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| excel-mcp-server | https://github.com/negokaz/excel-mcp-server | Yes |  |  |
| registry | https://github.com/modelcontextprotocol/registry | Yes |  |  |
| mcp-proxy | https://github.com/tbxark/mcp-proxy | Yes |  |  |
| mcp-filesystem-server | https://github.com/mark3labs/mcp-filesystem-server | No | AST_UNSUPPORTED_SDK_MACRO | AST parser enhancements for mark3labs/mcp-go tool registrations. |
| MCPJungle | https://github.com/mcpjungle/MCPJungle | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| kite-mcp-server | https://github.com/zerodha/kite-mcp-server | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| db-mcp-server | https://github.com/FreePeak/db-mcp-server | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-k8s-go | https://github.com/strowk/mcp-k8s-go | Yes |  |  |
| go-sdk | https://github.com/modelcontextprotocol/go-sdk | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| render-mcp-server | https://github.com/render-oss/render-mcp-server | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcptools | https://github.com/f/mcptools | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| whatsapp-mcp | https://github.com/verygoodplugins/whatsapp-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-link | https://github.com/automation-ai-labs/mcp-link | Yes |  |  |
| annas-mcp | https://github.com/iosifache/annas-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcprouter | https://github.com/chatmcp/mcprouter | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp | https://github.com/Teamwork/mcp | Yes |  |  |
| mcp-golang | https://github.com/metoro-io/mcp-golang | No | AST_UNSUPPORTED_SDK_MACRO | AST parser enhancements for mark3labs/mcp-go tool registrations. |
| razorpay-mcp-server | https://github.com/razorpay/razorpay-mcp-server | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| nightingale | https://github.com/ccfos/nightingale | Yes |  |  |
| signoz-mcp-server | https://github.com/SigNoz/signoz-mcp-server | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| gtm-mcp-server | https://github.com/paolobietolini/gtm-mcp-server | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| figma-mcp-go | https://github.com/RamenSV/figma-mcp-go | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| clihub | https://github.com/thellimist/clihub | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| weather-mcp-server | https://github.com/ezh0v/weather-mcp-server | Yes |  |  |
| k8s-mcp-server | https://github.com/reza-gholizade/k8s-mcp-server | Yes |  |  |
| caido-mcp-server | https://github.com/c0tton-fluff/caido-mcp-server | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| buildkite-mcp-server | https://github.com/buildkite/buildkite-mcp-server | Yes |  |  |
| toolhive | https://github.com/stacklok/toolhive | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| casdoor | https://github.com/casdoor/casdoor | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| loki-mcp | https://github.com/grafana/loki-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| yutu | https://github.com/eat-pray-ai/yutu | Yes |  |  |
| mcp-nomad | https://github.com/kocierik/mcp-nomad | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| openapi-to-mcpserver | https://github.com/higress-group/openapi-to-mcpserver | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-victoriametrics | https://github.com/VictoriaMetrics/mcp-victoriametrics | Yes |  |  |
| engram | https://github.com/Gentleman-Programming/engram | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-trino | https://github.com/tuannvm/mcp-trino | Yes |  |  |
| pgedge-postgres-mcp | https://github.com/pgEdge/pgedge-postgres-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| one-mcp | https://github.com/burugo/one-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| vault-mcp-server | https://github.com/hashicorp/vault-mcp-server | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-server | https://github.com/tektoncd/mcp-server | Yes |  |  |
| meshery-mcp-server | https://github.com/meshery-extensions/meshery-mcp-server | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-dap-server | https://github.com/go-delve/mcp-dap-server | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| openapi-mcp | https://github.com/ckanthony/openapi-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| ks-mcp-server | https://github.com/kubesphere/ks-mcp-server | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| code-sandbox-mcp | https://github.com/Automata-Labs-team/code-sandbox-mcp | No | BINARY_CONTAINER_ONLY | Support parsing binary / container images directly. |
| podman-mcp-server | https://github.com/manusa/podman-mcp-server | No | BINARY_CONTAINER_ONLY | Support parsing binary / container images directly. |
| prometheus-mcp | https://github.com/prometheus/prometheus-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| protoc-gen-go-mcp | https://github.com/redpanda-data/protoc-gen-go-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| kafka-mcp-server | https://github.com/tuannvm/kafka-mcp-server | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-auth-proxy | https://github.com/sigbit/mcp-auth-proxy | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-forge | https://github.com/achetronic/mcp-forge | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-victorialogs | https://github.com/VictoriaMetrics/mcp-victorialogs | Yes |  |  |
| pgmcp | https://github.com/subnetmarco/pgmcp | Yes |  |  |
| azure-cosmos-mcp-server-samples | https://github.com/AzureCosmosDB/azure-cosmos-mcp-server-samples | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-1c | https://github.com/feenlace/mcp-1c | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| reportportal-mcp-server | https://github.com/reportportal/reportportal-mcp-server | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-difyworkflow-server | https://github.com/gotoolkits/mcp-difyworkflow-server | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcpsnoop | https://github.com/kerlenton/mcpsnoop | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| kmcp | https://github.com/kagent-dev/kmcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-tts | https://github.com/blacktop/mcp-tts | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| gateway | https://github.com/centralmind/gateway | Yes |  |  |
| slack-mcp-client | https://github.com/tuannvm/slack-mcp-client | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| swagger-mcp | https://github.com/danishjsheikh/swagger-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| metoro-mcp-server | https://github.com/metoro-io/metoro-mcp-server | Yes |  |  |
| auto-mcp | https://github.com/brizzai/auto-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| agentdock | https://github.com/uvwt/agentdock | No | BINARY_CONTAINER_ONLY | Support parsing binary / container images directly. |
| toolhive-catalog | https://github.com/stacklok/toolhive-catalog | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-1panel | https://github.com/1Panel-dev/mcp-1panel | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-server-axiom | https://github.com/axiomhq/mcp-server-axiom | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-devtools | https://github.com/sammcj/mcp-devtools | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| vision-one-mcp-server | https://github.com/trendmicro/vision-one-mcp-server | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-client-go | https://github.com/yincongcyincong/mcp-client-go | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| last9-mcp-server | https://github.com/last9/last9-mcp-server | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| aks-mcp | https://github.com/Azure/aks-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-k6 | https://github.com/grafana/mcp-k6 | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| sandbox-mcp | https://github.com/pottekkat/sandbox-mcp | No | BINARY_CONTAINER_ONLY | Support parsing binary / container images directly. |
| xiaozhi-esp32-server-golang | https://github.com/hackers365/xiaozhi-esp32-server-golang | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| pixel-mcp | https://github.com/willibrandon/pixel-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-k8s | https://github.com/silenceper/mcp-k8s | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| skywalking-mcp | https://github.com/apache/skywalking-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcpgen | https://github.com/lyeslabs/mcpgen | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| jellyfin-mcp | https://github.com/jaredtrent/jellyfin-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-package-version | https://github.com/sammcj/mcp-package-version | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| memory-mcp-server-go | https://github.com/okooo5km/memory-mcp-server-go | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-shell | https://github.com/sonirico/mcp-shell | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| tunnel-client | https://github.com/openai/tunnel-client | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| forgejo-mcp | https://github.com/goern/forgejo-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-netbird | https://github.com/aantti/mcp-netbird | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| gentleman-book-mcp | https://github.com/Alan-TheGentleman/gentleman-book-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| gmail-mcp-server | https://github.com/PaulFidika/gmail-mcp-server | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| lazy-mcp | https://github.com/voicetreelab/lazy-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| things-cloud-mcp | https://github.com/wbopan/things-cloud-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-lifecycle-operator | https://github.com/kubernetes-sigs/mcp-lifecycle-operator | No | MONOREPO_NESTED_PATH | Monorepo scanning patterns for Go `/cmd/*` structures. |
| ah-mcp | https://github.com/mrserzhan/ah-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-boss-zp | https://github.com/namejiahui/mcp-boss-zp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| cpi-mcp-server | https://github.com/vadimklimov/cpi-mcp-server | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| n9e-mcp-server | https://github.com/n9e/n9e-mcp-server | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| forgejo-mcp | https://github.com/raohwork/forgejo-mcp | Yes |  |  |
| buttplug-mcp | https://github.com/ConAcademy/buttplug-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-server | https://github.com/TencentCloudCommunity/mcp-server | Yes |  |  |
| paprika-3-mcp | https://github.com/soggycactus/paprika-3-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| miro-mcp-server | https://github.com/olgasafonova/miro-mcp-server | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| tsidp | https://github.com/tailscale/tsidp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| gomcp | https://github.com/lightpanda-io/gomcp | Yes |  |  |
| kodit | https://github.com/helixml/kodit | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-gateway | https://github.com/hyprmcp/mcp-gateway | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| ophis | https://github.com/njayp/ophis | Yes |  |  |
| godoc-mcp | https://github.com/mrjoshuak/godoc-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-gateway | https://github.com/lucky-aeon/mcp-gateway | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcpshim | https://github.com/mcpshim/mcpshim | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| github-brain | https://github.com/wham/github-brain | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| chip | https://github.com/collibra/chip | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mysql-mcp-server | https://github.com/askdba/mysql-mcp-server | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-openweather | https://github.com/mschneider82/mcp-openweather | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-wecombot-server | https://github.com/gotoolkits/mcp-wecombot-server | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| bitrise-mcp | https://github.com/bitrise-io/bitrise-mcp | Yes |  |  |
| openings-mcp | https://github.com/amikai/openings-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| oauth-mcp-proxy | https://github.com/tuannvm/oauth-mcp-proxy | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-front | https://github.com/stainless-api/mcp-front | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| trivy-mcp | https://github.com/aquasecurity/trivy-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcpeserver | https://github.com/codehz/mcpeserver | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| ontap-mcp | https://github.com/NetApp/ontap-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| langcare-mcp-fhir | https://github.com/langcare/langcare-mcp-fhir | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| md2wechat-mcp-server | https://github.com/geekjourneyx/md2wechat-mcp-server | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| tasker-mcp | https://github.com/dceluis/tasker-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-gopls | https://github.com/hloiseau/mcp-gopls | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| litmus-mcp-server | https://github.com/litmuschaos/litmus-mcp-server | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| agent-lsp | https://github.com/blackwell-systems/agent-lsp | Yes |  |  |
| chronosphere-mcp | https://github.com/chronosphereio/chronosphere-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-cron | https://github.com/jolks/mcp-cron | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-nutanix | https://github.com/thunderboltsid/mcp-nutanix | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| FastDomainCheck-MCP-Server | https://github.com/bingal/FastDomainCheck-MCP-Server | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| ovn-kubernetes-mcp | https://github.com/ovn-kubernetes/ovn-kubernetes-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| linkwarden-mcp-server | https://github.com/irfansofyana/linkwarden-mcp-server | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-server | https://github.com/perses/mcp-server | Yes |  |  |
| fritzbox-mcp-server | https://github.com/kambriso/fritzbox-mcp-server | Yes |  |  |
| tempo-mcp-server | https://github.com/grafana-cold-storage/tempo-mcp-server | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| gitlab-mcp-server | https://github.com/jmrplens/gitlab-mcp-server | Yes |  |  |
| osv-mcp | https://github.com/StacklokLabs/osv-mcp | Yes |  |  |
| mcp-google-spreadsheet | https://github.com/kazz187/mcp-google-spreadsheet | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-kubernetes | https://github.com/Azure/mcp-kubernetes | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| api-wrapper-mcp | https://github.com/gomcpgo/api-wrapper-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| go-mcp-mysql | https://github.com/Zhwt/go-mcp-mysql | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| SecureMCP | https://github.com/makalin/SecureMCP | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mediawiki-mcp-server | https://github.com/olgasafonova/mediawiki-mcp-server | Yes |  |  |
| teamcity-mcp | https://github.com/itcaat/teamcity-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-prompt-server-go | https://github.com/smallnest/mcp-prompt-server-go | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-nats | https://github.com/sinadarbouy/mcp-nats | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| streamnative-mcp-server | https://github.com/streamnative/streamnative-mcp-server | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| gameguardian-mcp-server | https://github.com/giaoimgiao/gameguardian-mcp-server | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| feed-mcp | https://github.com/richardwooding/feed-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| minibridge | https://github.com/acuvity/minibridge | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| lfx-mcp | https://github.com/linuxfoundation/lfx-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| powhttp-mcp | https://github.com/usestring/powhttp-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| gemara-mcp | https://github.com/gemaraproj/gemara-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| toolhive-registry-server | https://github.com/stacklok/toolhive-registry-server | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| ig-mcp-server | https://github.com/inspektor-gadget/ig-mcp-server | No | BINARY_CONTAINER_ONLY | Support parsing binary / container images directly. |
| agent-memory-mcp | https://github.com/ipiton/agent-memory-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-zero | https://github.com/zeromicro/mcp-zero | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-gopls | https://github.com/Yantrio/mcp-gopls | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-server | https://github.com/aaPanel/mcp-server | Yes |  |  |
| mcp-k8s-eye | https://github.com/wenhuwang/mcp-k8s-eye | Yes |  |  |
| xiaoyuzhoufm-mcp | https://github.com/MosesHe/xiaoyuzhoufm-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| godoc-mcp-server | https://github.com/yikakia/godoc-mcp-server | Yes |  |  |
| gentle-ai | https://github.com/Gentleman-Programming/gentle-ai | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| xk6-mcp | https://github.com/grafana/xk6-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-tradovate | https://github.com/0xjmp/mcp-tradovate | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| umami-mcp-server | https://github.com/Macawls/umami-mcp-server | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-gitee | https://github.com/oschina/mcp-gitee | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| asgardeo-mcp-server | https://github.com/asgardeo/asgardeo-mcp-server | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-oauth-proxy | https://github.com/drpebcak/mcp-oauth-proxy | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp | https://github.com/DepsHubHQ/mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-unreal | https://github.com/remiphilippe/mcp-unreal | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-cyclops | https://github.com/cyclops-ui/mcp-cyclops | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| langchaingo-mcp-adapter | https://github.com/i2y/langchaingo-mcp-adapter | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| sysdig-mcp-server | https://github.com/sysdiglabs/sysdig-mcp-server | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| obs-mcp | https://github.com/rhobs/obs-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| systemd-mcp | https://github.com/openSUSE/systemd-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| miniflux-mcp | https://github.com/tssujt/miniflux-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| outlook-local-mcp | https://github.com/desek/outlook-local-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| altinity-mcp | https://github.com/Altinity/altinity-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| opentelemetry-mcp-server | https://github.com/pavolloffay/opentelemetry-mcp-server | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-web-ui | https://github.com/MegaGrindStone/mcp-web-ui | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| honeybadger-mcp-server | https://github.com/honeybadger-io/honeybadger-mcp-server | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| har-mcp | https://github.com/tjamet/har-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| things-cloud-mcp | https://github.com/mattydsmith/things-cloud-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| dolt-mcp | https://github.com/dolthub/dolt-mcp | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-server-proxy | https://github.com/leizongmin/mcp-server-proxy | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| sports-mcp-server | https://github.com/cloudbet/sports-mcp-server | Yes |  |  |
| dev-machine-guard | https://github.com/step-security/dev-machine-guard | No | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
