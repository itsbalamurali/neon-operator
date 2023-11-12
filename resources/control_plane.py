# A control plane api deployment with a service.
import kubernetes
import kopf

from kubernetes.client import V1ResourceRequirements, ApiException
import yaml

def deploy_control_plane(
        kube_client: kubernetes.client.CoreV1Api,
        namespace: str,
        replicas: int = 1,
        image: str = "ghcr.io/itsbalamurali/neon-operator:main",
        image_pull_policy: str = "IfNotPresent",
        resources: V1ResourceRequirements = None,
):
    deployment = control_plane_deployment(namespace, replicas, image, image_pull_policy, resources)
    kopf.adopt(deployment)
    service = control_plane_service(namespace)
    kopf.adopt(service)

    apps_client = kubernetes.client.AppsV1Api(kube_client)
    core_client = kubernetes.client.CoreV1Api(kube_client)
    try:
        apps_client.create_namespaced_deployment(namespace=namespace, body=deployment)
        core_client.create_namespaced_service(namespace=namespace, body=service)
    except ApiException as e:
        print("Exception when calling Api: %s\n" % e)

def update_control_plane(
        kube_client: kubernetes.client.ApiClient,
        namespace: str,
        replicas: int = 1,
        image: str = "ghcr.io/itsbalamurali/neon-operator:main",
        image_pull_policy: str = "IfNotPresent",
        resources: V1ResourceRequirements = None,
):
    deployment = control_plane_deployment(namespace, replicas, image, image_pull_policy, resources)
    kopf.adopt(deployment)
    service = control_plane_service(namespace)
    kopf.adopt(service)

    apps_client = kubernetes.client.AppsV1Api(kube_client)
    core_client = kubernetes.client.CoreV1Api(kube_client)
    try:
        apps_client.patch_namespaced_deployment(namespace=namespace, name="control-plane", body=deployment)
        core_client.patch_namespaced_service(namespace=namespace, name="control-plane", body=service)
    except ApiException as e:
        print("Exception when calling Api: %s\n" % e)

def delete_control_plane(
        kube_client: kubernetes.client.ApiClient,
        namespace: str,
):
    apps_client = kubernetes.client.AppsV1Api(kube_client)
    core_client = kubernetes.client.CoreV1Api(kube_client)
    try:
        apps_client.delete_namespaced_deployment(namespace=namespace, name="control-plane")
        core_client.delete_namespaced_service(namespace=namespace, name="control-plane")
    except ApiException as e:
        print("Exception when calling Api: %s\n" % e)

def control_plane_deployment(
        namespace: str,
        replicas: int,
        image: str,
        image_pull_policy: str,
        resources: V1ResourceRequirements,
) -> kubernetes.client.V1Deployment:
    deployment = kubernetes.client.V1Deployment(
        api_version="apps/v1",
        kind="Deployment",
        metadata=kubernetes.client.V1ObjectMeta(
            name="control-plane",
            namespace=namespace,
            labels={"app": "control-plane"},
        ),
        spec=kubernetes.client.V1DeploymentSpec(
        replicas=replicas,
        selector=kubernetes.client.V1LabelSelector(
            match_labels={"app": "control-plane"},
        ),
        template=kubernetes.client.V1PodTemplateSpec(
        metadata=kubernetes.client.V1ObjectMeta(
            labels={"app": "control-plane"},
        ),
        spec=kubernetes.client.V1PodSpec(
            containers=[
                kubernetes.client.V1Container(
                    name="control-plane",
                    image=image,
                    image_pull_policy=image_pull_policy,
                    ports=[
                        kubernetes.client.V1ContainerPort(
                            container_port=1234,
                            name="http",
                        ),
                    ],
                    command=["uvicorn", "control_plane_server:app", "--host", "0.0.0.0", "--port", "1234"],
                    resources=resources,
                ),
            ],
        ),
    ),
    ),
    )

    print(yaml.dump(deployment))
    return deployment


def control_plane_service(
        namespace: str,
) -> kubernetes.client.V1Service:
    service = kubernetes.client.V1Service(
        api_version="v1",
        kind="Service",
        metadata=kubernetes.client.V1ObjectMeta(
            name="control-plane",
            namespace=namespace,
            labels={"app": "control-plane"},
        ),
        spec=kubernetes.client.V1ServiceSpec(
            selector={"app": "control-plane"},
            ports=[
                kubernetes.client.V1ServicePort(
                    name="http",
                    port=1234,
                    target_port=1234,
                ),
            ],
        ),
    )

    return service
