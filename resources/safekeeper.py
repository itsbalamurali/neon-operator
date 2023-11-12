# Create a safekeeper statefulset, service, and persistent volume claim.
from typing import Any

import kopf
import kubernetes
from kubernetes.client import V1ResourceRequirements, ApiException


def deploy_safekeeper(
        kube_client: kubernetes.client.ApiClient,
        namespace: str,
        resources: V1ResourceRequirements,
        remote_storage_bucket_endpoint: Any,
        remote_storage_bucket_name: Any,
        remote_storage_bucket_region: Any,
        remote_storage_prefix_in_bucket: Any = None,
        image_pull_policy: str = "IfNotPresent",
        image: str = "neondatabase/neon",
        replicas: int = 3,
):
    deployment = safekeeper_statefulset(namespace=namespace, resources=resources,
                                        remote_storage_bucket_endpoint=remote_storage_bucket_endpoint,
                                        remote_storage_bucket_name=remote_storage_bucket_name,
                                        remote_storage_bucket_region=remote_storage_bucket_region,
                                        remote_storage_prefix_in_bucket=remote_storage_prefix_in_bucket,
                                        image_pull_policy=image_pull_policy, image=image, replicas=replicas)
    kopf.adopt(deployment)
    service = safekeeper_service(namespace)
    kopf.adopt(service)
    # pvc = safekeeper_pvc(namespace)

    apps_client = kubernetes.client.AppsV1Api(kube_client)
    core_client = kubernetes.client.CoreV1Api(kube_client)
    try:
        apps_client.create_namespaced_stateful_set(namespace=namespace, body=deployment)
        core_client.create_namespaced_service(namespace=namespace, body=service)
        # core_client.create_namespaced_persistent_volume_claim(namespace=namespace, body=pvc)
    except ApiException as e:
        print("Exception when calling Api: %s\n" % e)


def update_safekeeper(
        kube_client: kubernetes.client.ApiClient,
        namespace: str,
        resources: V1ResourceRequirements,
        remote_storage_bucket_endpoint: Any,
        remote_storage_bucket_name: Any,
        remote_storage_bucket_region: Any,
        remote_storage_prefix_in_bucket: Any = None,
        image_pull_policy: str = "IfNotPresent",
        image: str = "neondatabase/neon",
        replicas: int = 3,
):
    deployment = safekeeper_statefulset(namespace=namespace, resources=resources,
                                        remote_storage_bucket_endpoint=remote_storage_bucket_endpoint,
                                        remote_storage_bucket_name=remote_storage_bucket_name,
                                        remote_storage_bucket_region=remote_storage_bucket_region,
                                        remote_storage_prefix_in_bucket=remote_storage_prefix_in_bucket,
                                        image_pull_policy=image_pull_policy, image=image, replicas=replicas)
    kopf.adopt(deployment)
    service = safekeeper_service(namespace)
    kopf.adopt(service)
    # pvc = safekeeper_pvc(namespace)

    apps_client = kubernetes.client.AppsV1Api(kube_client)
    core_client = kubernetes.client.CoreV1Api(kube_client)
    try:
        apps_client.patch_namespaced_stateful_set(namespace=namespace, name="safekeeper", body=deployment)
        core_client.patch_namespaced_service(namespace=namespace, name="safekeeper", body=service)
    except ApiException as e:
        print("Exception when calling Api: %s\n" % e)


def delete_safekeeper(
        kube_client: kubernetes.client.ApiClient,
        namespace: str,
):
    apps_client = kubernetes.client.AppsV1Api(kube_client)
    core_client = kubernetes.client.CoreV1Api(kube_client)
    try:
        apps_client.delete_namespaced_stateful_set(namespace=namespace, name="safekeeper")
        core_client.delete_namespaced_service(namespace=namespace, name="safekeeper")
        # core_client.delete_namespaced_persistent_volume_claim(namespace=namespace, name="safekeeper")
    except ApiException as e:
        print("Exception when calling Api: %s\n" % e)


def safekeeper_statefulset(
        namespace: str,
        resources: V1ResourceRequirements,
        remote_storage_bucket_endpoint: Any,
        remote_storage_bucket_name: Any,
        remote_storage_bucket_region: Any,
        remote_storage_prefix_in_bucket: Any,
        image_pull_policy: str,
        image: str,
        replicas: int) -> kubernetes.client.V1StatefulSet:
    template = kubernetes.client.V1PodTemplateSpec(
        metadata=kubernetes.client.V1ObjectMeta(
            labels={"app": "safekeeper"},
        ),
        spec=kubernetes.client.V1PodSpec(
            containers=[
                kubernetes.client.V1Container(
                    name="safekeeper",
                    image=image,
                    image_pull_policy=image_pull_policy,
                    resources=resources,
                    command=[
                        "safekeeper",
                        "--listen-pg=0.0.0.0:5454",
                        "--listen-http=0.0.0.0:7676",
                        "--id=$(SAFEKEEPER_ID)",
                        "--broker-endpoint=http://storage-broker." + namespace + ".svc.cluster.local:50051",
                        "-D",
                        "/data",
                        f"--remote-storage={{endpoint='{remote_storage_bucket_endpoint}',bucket_name='{remote_storage_bucket_name}',bucket_region='{remote_storage_bucket_region}',prefix_in_bucket='{remote_storage_prefix_in_bucket}'}}"
                    ],
                    readiness_probe=kubernetes.client.V1Probe(
                        http_get=kubernetes.client.V1HTTPGetAction(
                            path="/v1/status",
                            port=7676,
                        ),
                        initial_delay_seconds=5,
                        period_seconds=5,
                    ),
                    env=[
                        # NOTE: Only works with kubernetes 1.28+
                        kubernetes.client.V1EnvVar(
                            name="SAFEKEEPER_ID",
                            value_from=kubernetes.client.V1EnvVarSource(
                                field_ref=kubernetes.client.V1ObjectFieldSelector(
                                    field_path="metadata.labels['apps.kubernetes.io/pod-index']",
                                ),
                            ),
                        ),
                        kubernetes.client.V1EnvVar(
                            name="AWS_ACCESS_KEY_ID",
                            value_from=kubernetes.client.V1EnvVarSource(
                                secret_key_ref=kubernetes.client.V1SecretKeySelector(
                                    key="AWS_ACCESS_KEY_ID",
                                    name="neon-storage-credentials",
                                ),
                            ),
                        ),
                        kubernetes.client.V1EnvVar(
                            name="AWS_SECRET_ACCESS_KEY",
                            value_from=kubernetes.client.V1EnvVarSource(
                                secret_key_ref=kubernetes.client.V1SecretKeySelector(
                                    key="AWS_SECRET_ACCESS_KEY",
                                    name="neon-storage-credentials",
                                ),
                            ),
                        ),
                    ],
                    ports=[
                        kubernetes.client.V1ContainerPort(container_port=5454),
                        kubernetes.client.V1ContainerPort(container_port=7676),
                    ],
                    # volume_mounts=[
                    #     kubernetes.client.V1VolumeMount(
                    #         name="safekeeper-data-volume",
                    #         mount_path="/data",
                    #     ),
                    # ],
                ),
            ],
            # volumes=[
            #     kubernetes.client.V1Volume(
            #         name="safekeeper-data-volume",
            #         persistent_volume_claim=kubernetes.client.V1PersistentVolumeClaimVolumeSource(
            #             claim_name="safekeeper-data-volume",
            #         ),
            #     ),
            # ]
        ),
    )

    deployment = kubernetes.client.V1StatefulSet(
        api_version="apps/v1",
        kind="StatefulSet",
        metadata=kubernetes.client.V1ObjectMeta(
            name="safekeeper",
            namespace=namespace,
            labels={"app": "safekeeper"},
        ),
        spec=kubernetes.client.V1StatefulSetSpec(
            replicas=replicas,
            service_name="safekeeper",
            selector=kubernetes.client.V1LabelSelector(
                match_labels={"app": "safekeeper"},
            ),
            template=template,
        )
    )

    return deployment


def safekeeper_service(
        namespace: str,
) -> kubernetes.client.V1Service:
    service = kubernetes.client.V1Service(
        api_version="v1",
        kind="Service",
        metadata=kubernetes.client.V1ObjectMeta(
            name="safekeeper",
            namespace=namespace,
        ),
        spec=kubernetes.client.V1ServiceSpec(
            selector={"app": "safekeeper"},
            ports=[
                kubernetes.client.V1ServicePort(
                    port=5454,
                    name="wal",
                    target_port=5454,
                ),
                kubernetes.client.V1ServicePort(
                    port=7676,
                    name="http",
                    target_port=7676,
                ),
            ],
        ),
    )

    return service


def safekeeper_pvc(
        namespace: str,
        storage: str = "1Gi",
        access_modes=None
) -> kubernetes.client.V1PersistentVolumeClaim:
    if access_modes is None:
        access_modes = ["ReadWriteOnce"]
    pvc = kubernetes.client.V1PersistentVolumeClaim(
        api_version="v1",
        kind="PersistentVolumeClaim",
        metadata=kubernetes.client.V1ObjectMeta(
            name="safekeeper-data-volume",
            namespace=namespace,
        ),
        spec=kubernetes.client.V1PersistentVolumeClaimSpec(
            access_modes=access_modes,
            resources=kubernetes.client.V1ResourceRequirements(
                requests={"storage": storage},
            ),
        ),
    )

    return pvc
