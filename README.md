# Neon Serverless Postgres K8S Operator

## License

[MIT License](./LICENSE)

[Neon is licensed under Apache License 2.0](https://github.com/neondatabase/neon/blob/main/LICENSE).

Only use this code if you know what you are doing legally in agreement with NEON's license.

When NeonDeployment is created:
Step 1: Launch Storage Broker
Step 2: Launch SafeKeepers with above storage broker
When Tenant is Created (Create a default timeline along with tenant):
Step 1: Launch PageServer with tenant mapped to it (persist the pageserver id with new tenant and pageserver gets it via /re-attach request)
Step 2: Launch Compute Node Mapping a pageserver ()
When a timeline is created(Mapped with Tenant)

## TODO:

- [ ] Launch ComputeNodes & PageServer based on the Tenants in Co-ordination with Control Panel Server.
- [ ] CertManager for TLS.
- [ ] JWT Auth Between the components.
- [ ] Control Plane API Implementation (Work in Progress).
- [ ] Tenants & Timelines management via CRD (Work in Progress).
- [ ] Autoscaler Agent Support.
- [ ] Implement Authentication (/authenticate_proxy_request/) Service required by Proxy Server(This service is not open-sourced by neon).
- [ ] Proxy Server Support (Not really useful unless you are on constrained env like WASM!!!)
- [ ] Add NEON_CONTROL_PLANE_TOKEN env on compute-node.
