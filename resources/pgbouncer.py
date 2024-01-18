import kopf
import kubernetes
from kubernetes.client import V1ResourceRequirements, ApiException


def deploy_pgbouncer(
        namespace: str,
):
    """
    Deploy the pgbouncer proxy to the cluster
    :return:
    """
    deployment = pgbouncer_deployment()
    service = pgbouncer_service()
    kopf.adopt(deployment)
    kopf.adopt(service)

    apps_client = kubernetes.client.AppsV1Api()
    core_client = kubernetes.client.CoreV1Api()
    try:
        apps_client.create_namespaced_deployment(namespace=namespace, body=deployment)
        core_client.create_namespaced_service(namespace=namespace, body=service)
    except ApiException as e:
        print("Exception when calling Api: %s\n" % e)


def update_pgbouncer(
        namespace: str,
):
    deployment = pgbouncer_deployment()
    service = pgbouncer_service()
    kopf.adopt(deployment)
    kopf.adopt(service)

    apps_client = kubernetes.client.AppsV1Api()
    core_client = kubernetes.client.CoreV1Api()
    try:
        apps_client.patch_namespaced_deployment(namespace=namespace, name="pgbouncer", body=deployment)
        core_client.patch_namespaced_service(namespace=namespace, name="pgbouncer", body=service)
    except ApiException as e:
        print("Exception when calling Api: %s\n" % e)


def delete_pgbouncer(
        namespace: str,
):
    apps_client = kubernetes.client.AppsV1Api()
    core_client = kubernetes.client.CoreV1Api()
    try:
        apps_client.delete_namespaced_deployment(namespace=namespace, name="pgbouncer")
        core_client.delete_namespaced_service(namespace=namespace, name="pgbouncer")
    except ApiException as e:
        print("Exception when calling Api: %s\n" % e)


def pgbouncer_deployment(
        namespace: str,
        resources: V1ResourceRequirements,
        image: str = "bitnami/pgbouncer:latest",
        replicas: int = 1,

) -> kubernetes.client.V1Deployment:
    """
    Generate a deployment for the pgbouncer proxy
    :return:
    """
    return kubernetes.client.V1Deployment(
        api_version="apps/v1",
        kind="Deployment",
        metadata=kubernetes.client.V1ObjectMeta(
            name="pgbouncer",
            namespace=namespace,
            labels={
                "app": "pgbouncer",
            },
        ),
        spec=kubernetes.client.V1DeploymentSpec(
            replicas=1,
            selector=kubernetes.client.V1LabelSelector(
                match_labels={
                    "app": "pgbouncer",
                },
            ),
            template=kubernetes.client.V1PodTemplateSpec(
                metadata=kubernetes.client.V1ObjectMeta(
                    labels={
                        "app": "pgbouncer",
                    },
                ),
                spec=kubernetes.client.V1PodSpec(
                    containers=[
                        kubernetes.client.V1Container(
                            name="pgbouncer",
                            image=image,
                            ports=[
                                kubernetes.client.V1ContainerPort(
                                    container_port=5432,
                                ),
                            ],
                            resources=resources,
                            env=[
                                kubernetes.client.V1EnvVar(
                                    name="POSTGRESQL_HOST",
                                    value=f"postgres-compute.{namespace}.svc.cluster.local:5432",
                                ),
                                kubernetes.client.V1EnvVar(
                                    name="PGBOUNCER_AUTH_TYPE",
                                    value="trust",
                                ),
                            ],
                        ),
                        kubernetes.client.V1Container(
                            name="pgbouncer-metrics",
                            image="prometheuscommunity/pgbouncer-exporter:latest",
                            ports=[
                                kubernetes.client.V1ContainerPort(
                                    container_port=9127,
                                ),
                            ],
                            resources=kubernetes.client.V1ResourceRequirements(
                                requests={
                                    "cpu": "100m",
                                    "memory": "100Mi",
                                },
                                limits={
                                    "cpu": "100m",
                                    "memory": "100Mi",
                                },
                            ),
                        )
                    ],
                ),
            ),
        ),
    )


def pgbouncer_configmap(
        namespace: str,
) -> kubernetes.client.V1ConfigMap:
    """
    Generate a configmap for the pgbouncer proxy
    :return:
    """
    return kubernetes.client.V1ConfigMap(
        api_version="v1",
        kind="ConfigMap",
        metadata=kubernetes.client.V1ObjectMeta(
            name="pgbouncer",
            namespace=namespace,
            labels={
                "app": "pgbouncer",
            },
        ),
        data={
            "pgbouncer.ini": """
[databases]
* = host=postgres port=5432
}
""",
            "userlist.txt": """
"postgres" "postgres"
""",
        },
    )


def pgbouncer_service(
        namespace: str,
) -> kubernetes.client.V1Service:
    """
    Generate a service for the pgbouncer proxy
    :return:
    """
    return kubernetes.client.V1Service(
        api_version="v1",
        kind="Service",
        metadata=kubernetes.client.V1ObjectMeta(
            name="pgbouncer",
            namespace=namespace,
            labels={
                "app": "pgbouncer",
            },
        ),
        spec=kubernetes.client.V1ServiceSpec(
            selector={
                "app": "pgbouncer",
            },
            ports=[
                kubernetes.client.V1ServicePort(
                    port=5432,
                    name="pgbouncer",
                    target_port=5432,
                ),
                kubernetes.client.V1ServicePort(
                    port=6432,
                    name="pgbouncer-metrics",
                    target_port=6432,
                ),
            ],
        ),
    )
