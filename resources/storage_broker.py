import kopf
import kubernetes
from kubernetes.client import ApiException


def deploy_storage_broker(
        kube_client: kubernetes.client.ApiClient,
        namespace: str,
        image: str = "neondatabase/neon:latest",
        replicas: int = 1,
):
    deployment = storage_broker_deployment(namespace, image, replicas)
    service = storage_broker_service(namespace)
    kopf.adopt(deployment)
    kopf.adopt(service)

    apps_client = kubernetes.client.AppsV1Api(kube_client)
    core_client = kubernetes.client.CoreV1Api(kube_client)
    try:
        apps_client.create_namespaced_deployment(namespace=namespace, body=deployment)
        core_client.create_namespaced_service(namespace=namespace, body=service)
    except ApiException as e:
        print("Exception when calling Api: %s\n" % e)

def update_storage_broker(
        kube_client: kubernetes.client.ApiClient,
        namespace: str,
        image: str = "neondatabase/neon:latest",
        replicas: int = 1,
):
    deployment = storage_broker_deployment(namespace, image, replicas)
    service = storage_broker_service(namespace)
    kopf.adopt(deployment)
    kopf.adopt(service)

    apps_client = kubernetes.client.AppsV1Api(kube_client)
    core_client = kubernetes.client.CoreV1Api(kube_client)
    try:
        apps_client.patch_namespaced_deployment(namespace=namespace, name="storage-broker", body=deployment)
        core_client.patch_namespaced_service(namespace=namespace, name="storage-broker", body=service)
    except ApiException as e:
        print("Exception when calling Api: %s\n" % e)

def delete_storage_broker(
        kube_client: kubernetes.client.ApiClient,
        namespace: str,
):
    apps_client = kubernetes.client.AppsV1Api(kube_client)
    core_client = kubernetes.client.CoreV1Api(kube_client)
    try:
        apps_client.delete_namespaced_deployment(namespace=namespace, name="storage-broker")
        core_client.delete_namespaced_service(namespace=namespace, name="storage-broker")
    except ApiException as e:
        print("Exception when calling Api: %s\n" % e)

def storage_broker_deployment(
        namespace: str,
        image: str,
        replicas: int,
) -> kubernetes.client.V1Deployment:
    template = kubernetes.client.V1PodTemplateSpec(
        metadata=kubernetes.client.V1ObjectMeta(
            labels={"app": "storage-broker"},
        ),
        spec=kubernetes.client.V1PodSpec(
            containers=[
                kubernetes.client.V1Container(
                    name="storage-broker",
                    image=image,
                    command=["storage_broker", "--listen-addr=0.0.0.0:50051"],
                    ports=[
                        kubernetes.client.V1ContainerPort(
                            container_port=50051,
                            name="grpc",
                        ),
                    ],
                ),
            ],
        ),
    )

    spec = kubernetes.client.V1DeploymentSpec(
        replicas=replicas,
        selector=kubernetes.client.V1LabelSelector(
            match_labels={"app": "storage-broker"},
        ),
        template=template,
    )

    deployment = kubernetes.client.V1Deployment(
        api_version="apps/v1",
        kind="Deployment",
        metadata=kubernetes.client.V1ObjectMeta(
            name="storage-broker",
            namespace=namespace,
            labels={"app": "storage-broker"},
        ),
        spec=spec,
    )

    return deployment


def storage_broker_service(
        namespace: str,
) -> kubernetes.client.V1Service:
    service = kubernetes.client.V1Service(
        api_version="v1",
        kind="Service",
        metadata=kubernetes.client.V1ObjectMeta(
            name="storage-broker",
            namespace=namespace,
            labels={"app": "storage-broker"},
        ),
        spec=kubernetes.client.V1ServiceSpec(
            selector={"app": "storage-broker"},
            ports=[
                kubernetes.client.V1ServicePort(
                    port=50051,
                    target_port=50051,
                    name="grpc",
                ),
            ],
        ),
    )

    return service
