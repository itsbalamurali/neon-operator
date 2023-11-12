# Create compute-node deployment with 3 replicas
import kopf
import kubernetes
from kubernetes.client import V1ResourceRequirements, ApiException, V1StatefulSet
import yaml


def deploy_compute_node(
        kube_client: kubernetes.client.ApiClient,
        namespace: str,
        # replicas: int = 3,
        image: str = "neondatabase/compute-node-v16:latest",
        image_pull_policy: str = "IfNotPresent",
        extensions_bucket: str = "neon-dev-extensions-eu-central-1",
        extensions_bucket_region: str = "eu-central-1",
        resources: V1ResourceRequirements = None,
):
    statefulset: V1StatefulSet = compute_node_deployment(namespace=namespace,
                                                         image=image,
                                                         image_pull_policy=image_pull_policy,
                                                         extensions_bucket=extensions_bucket,
                                                         # replicas=replicas,
                                                         extensions_bucket_region=extensions_bucket_region,
                                                         resources=resources)
    kopf.adopt(statefulset)
    service = compute_node_service(namespace)
    kopf.adopt(service)

    apps_client = kubernetes.client.AppsV1Api(kube_client)
    core_client = kubernetes.client.CoreV1Api(kube_client)
    try:
        apps_client.create_namespaced_stateful_set(namespace=namespace, body=statefulset)
        core_client.create_namespaced_service(namespace=namespace, body=service)
    except ApiException as e:
        print("Exception when calling Api: %s\n" % e)


def update_compute_node(
        kube_client: kubernetes.client.ApiClient,
        namespace: str,
        # replicas: int = 3,
        image: str = "neondatabase/compute-node-v16:latest",
        image_pull_policy: str = "IfNotPresent",
        extensions_bucket: str = "neon-dev-extensions-eu-central-1",
        extensions_bucket_region: str = "eu-central-1",
        resources: V1ResourceRequirements = None,
):
    statefulset = compute_node_deployment(namespace=namespace,
                                          image=image,
                                          image_pull_policy=image_pull_policy,
                                          extensions_bucket=extensions_bucket,
                                          # replicas=replicas,
                                          extensions_bucket_region=extensions_bucket_region,
                                          resources=resources)
    kopf.adopt(statefulset)
    service = compute_node_service(namespace)
    kopf.adopt(service)

    apps_client = kubernetes.client.AppsV1Api(kube_client)
    core_client = kubernetes.client.CoreV1Api(kube_client)
    try:
        apps_client.patch_namespaced_stateful_set(namespace=namespace, name="compute-node", body=statefulset)
        core_client.patch_namespaced_service(namespace=namespace, name="compute-node", body=service)
    except ApiException as e:
        print("Exception when calling Api: %s\n" % e)


def delete_compute_node(
        kube_client: kubernetes.client.ApiClient,
        namespace: str,
):
    apps_client = kubernetes.client.AppsV1Api(kube_client)
    core_client = kubernetes.client.CoreV1Api(kube_client)
    try:
        apps_client.delete_namespaced_deployment(namespace=namespace, name="compute-node")
        core_client.delete_namespaced_config_map(namespace=namespace, name="compute-node-config")
        core_client.delete_namespaced_service(namespace=namespace, name="compute-node")
    except ApiException as e:
        print("Exception when calling Api: %s\n" % e)


def compute_node_deployment(
        namespace: str,
        image: str,
        image_pull_policy: str,
        extensions_bucket: str,
        extensions_bucket_region: str,
        resources: V1ResourceRequirements = None,
        replicas: int = 3,
        storage_capacity: str = "1Gi",
) -> kubernetes.client.V1StatefulSet:
    statefulset = kubernetes.client.V1StatefulSet(
        api_version="apps/v1",
        kind="StatefulSet",
        metadata=kubernetes.client.V1ObjectMeta(
            name="compute-node",
            namespace=namespace,
            labels={"app": "compute-node"},
        ),
        spec=kubernetes.client.V1StatefulSetSpec(
            replicas=replicas,
            service_name="compute-node",
            selector=kubernetes.client.V1LabelSelector(
                match_labels={"app": "compute-node"},
            ),
            template=kubernetes.client.V1PodTemplateSpec(
                metadata=kubernetes.client.V1ObjectMeta(
                    labels={"app": "compute-node"},
                ),
                spec=kubernetes.client.V1PodSpec(
                    containers=[
                        kubernetes.client.V1Container(
                            name="compute-node",
                            image=image,
                            image_pull_policy=image_pull_policy,
                            ports=[
                                kubernetes.client.V1ContainerPort(
                                    container_port=5432,
                                    name="pg",
                                ),
                                kubernetes.client.V1ContainerPort(
                                    container_port=3080,
                                    name="http",
                                ),
                            ],
                            command=["compute_ctl",
                                     "--pgdata", "/var/db/postgres/compute",
                                     "--connstr", "postgresql://cloud_admin@0.0.0.0:5432/postgres",
                                     "--pgbin", "/usr/local/bin/postgres",
                                     "--remote-ext-config", f"{{\"bucket\":\"{extensions_bucket}\",\"region\":\"{extensions_bucket_region}\"}}",
                                     "--control-plane-uri", f"http://control-plane.{namespace}.svc.cluster.local:1234"
                                     "--compute-id", "$(COMPUTE_ID)"],
                            env=[
                                # NOTE: Only works with kubernetes 1.28+
                                kubernetes.client.V1EnvVar(
                                    name="COMPUTE_ID",
                                    value_from=kubernetes.client.V1EnvVarSource(
                                        field_ref=kubernetes.client.V1ObjectFieldSelector(
                                            field_path="metadata.labels['apps.kubernetes.io/pod-index']",
                                        ),
                                    ),
                                )],
                            volume_mounts=[
                                kubernetes.client.V1VolumeMount(
                                    name="compute-node-data-volume",
                                    mount_path="/data/.neon/",
                                ),
                            ],
                            resources=resources,
                        ),
                    ],
                    volumes=[
                        kubernetes.client.V1Volume(
                            name="compute-node-data-volume",
                            persistent_volume_claim=kubernetes.client.V1PersistentVolumeClaimVolumeSource(
                                claim_name="compute-node-data-volume",
                            ),
                        ),
                    ],
                ),
            ),
            volume_claim_templates=[
                kubernetes.client.V1PersistentVolumeClaim(
                    metadata=kubernetes.client.V1ObjectMeta(
                        name="compute-node-data-volume",
                        namespace=namespace,
                        labels={"app": "compute-node"},
                    ),
                    spec=kubernetes.client.V1PersistentVolumeClaimSpec(
                        access_modes=["ReadWriteOnce"],
                        resources=kubernetes.client.V1ResourceRequirements(
                            requests={"storage": storage_capacity},
                        ),
                    ),
                ),
            ],
        ),
    )

    return statefulset


def compute_node_service(
        namespace: str,
) -> kubernetes.client.V1Service:
    service = kubernetes.client.V1Service(
        api_version="v1",
        kind="Service",
        metadata=kubernetes.client.V1ObjectMeta(
            name="compute-node",
            namespace=namespace,
            labels={"app": "compute-node"},
        ),
        spec=kubernetes.client.V1ServiceSpec(
            selector={"app": "compute-node"},
            ports=[
                kubernetes.client.V1ServicePort(
                    port=5432,
                    target_port=5432,
                    name="pg",
                ),
                kubernetes.client.V1ServicePort(
                    port=3080,
                    target_port=3080,
                    name="http",
                ),
            ],
        ),
    )

    return service
