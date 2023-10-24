# Neon Serverless Postgres Helm Chart

This Helm chart deploys a Neon serverless Postgres database.

## License
While this chart is [MIT License](./LICENSE), [Neon is licensed as Apache License 2.0](https://github.com/neondatabase/neon/blob/main/LICENSE).
Only use this chart if you know what you are doing legally in agreement with NEON's license.

## Prerequisites

Before deploying this chart, you must have the following:

- A K8s cluster.
- Helm 3 installed

## Installing the Chart

```bash
helm repo add neondatabase https://itsbalamurali.github.io/neon
```

To install the chart, run the following command:

```bash
helm install <release-name> neondatabase/neon
```

## TODO:
[] Cleanup (variables and values etc., currently there is a bunch of hardcoded stuff)
[] Metrics (PodMonitor)
[] Create a control-plane operator to be able to control tenants and their timelines using k8s crds and store the state to etcd.