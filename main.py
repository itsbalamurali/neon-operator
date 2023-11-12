import kopf
import logging
import kubernetes
import requests
import resources.common
import resources.compute_node
import resources.control_plane
import resources.pageserver
import resources.safekeeper
import resources.storage_broker
import resources.autoscaler_agent


@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    settings.posting.level = logging.ERROR
    settings.networking.connect_timeout = 10
    settings.networking.request_timeout = 60
    settings.watching.server_timeout = 10 * 60
    settings.persistence.finalizer = 'neon.tech/neon-finalizer'
    settings.persistence.progress_storage = kopf.MultiProgressStorage([
        kopf.AnnotationsProgressStorage(prefix='neon.tech'),
        kopf.StatusProgressStorage(field='status.neon-operator'),
    ])


@kopf.on.startup()
async def startup(logger, **kwargs):
    logger.info("Startup completed.")


def default_resource_limits():
    return kubernetes.client.V1ResourceRequirements(
        requests={
            "cpu": "100m",
            "memory": "200Mi",
        },
        limits={
            "cpu": "100m",
            "memory": "200Mi",
        },
    )

@kopf.on.create("neontenants")
def create_tenant(spec, name, namespace,**_):
    kopf.info(spec,reason='CreatingTenant',message=f'Creating {namespace}/{name}.')
    kubernetes.config.load_incluster_config()
    kube_client = kubernetes.client.ApiClient()
    check_for_pageserver(kube_client, namespace, name)
    pageserver_url = f"http://pageserver.{namespace}.svc.cluster.local:6400"
    # Call the api to create the tenant using requests post method to pageserver_url/v1/tenant
    # If the response is not 200, raise kopf.PermanentError(f"Failed to create tenant {namespace}/{name}")
    # If the response is 200, kopf.adopt the tenant
    request = {}
    response = requests.post(f"{pageserver_url}/v1/tenant", json=request)
    if response.status_code != 200:
        raise kopf.PermanentError(f"Failed to create tenant {namespace}/{name}")
    else:
        tenant_id = response.text
    kopf.info(spec,reason='CreatingTenant',message=f'Created {namespace}/{name}/{tenant_id}.')
    kopf.adopt(spec)



@kopf.on.update("neontenants")
def update_tenant(spec, name, namespace, **_):
    kopf.info(spec,reason='UpdatingTenant',message=f'Updating {namespace}/{name}.')
    kubernetes.config.load_incluster_config()
    kube_client = kubernetes.client.ApiClient()
    check_for_pageserver(kube_client, namespace, name)
    pageserver_url = f"http://pageserver.{namespace}.svc.cluster.local:6400"
    # Call the api to update the tenant
    request = {}
    response = requests.put(f"{pageserver_url}/v1/tenant/config", json=request)


@kopf.on.delete("neontenants")
def delete_tenant(spec, name, namespace,**_):
    kopf.info(spec,reason='DeletingTenant',message=f'Deleting {namespace}/{name}.')
    kubernetes.config.load_incluster_config()
    kube_client = kubernetes.client.ApiClient()
    check_for_pageserver(kube_client, namespace, name)
    pageserver_url = f"http://pageserver.{namespace}.svc.cluster.local:6400"


@kopf.on.create("neontimelines")
def create_timeline(spec, name, namespace,**_):
    kopf.info(spec,reason='CreatingTimeline',message=f'Creating {namespace}/{name}.')
    kubernetes.config.load_incluster_config()
    kube_client = kubernetes.client.ApiClient()
    check_for_pageserver(kube_client, namespace, name)
    pageserver_url = f"http://pageserver.{namespace}.svc.cluster.local:6400"
    # Call the api to create the timeline
    request = {}
    response = requests.post(f"{pageserver_url}/v1/timeline", json=request)
    if response.status_code != 200:
        raise kopf.PermanentError(f"Failed to create timeline {namespace}/{name}")
    else:
        timeline_id = response.text
    kopf.info(spec,reason='CreatingTimeline',message=f'Created {namespace}/{name}/{timeline_id}.')
    kopf.adopt(spec)

@kopf.on.update("neontimelines")
def update_timeline(spec, name, namespace, **_):
    kopf.info(spec,reason='UpdatingTimeline',message=f'Updating {namespace}/{name}.')
    kubernetes.config.load_incluster_config()
    kube_client = kubernetes.client.ApiClient()
    check_for_pageserver(kube_client, namespace, name)
    pageserver_url = f"http://pageserver.{namespace}.svc.cluster.local:6400"
    # Call the api to update the timeline
    request = {}
    response = requests.put(f"{pageserver_url}/v1/timeline", json=request)


@kopf.on.delete("neontimelines")
def delete_timeline(spec, name, namespace,**_):
    kopf.info(spec,reason='DeletingTimeline',message=f'Deleting {namespace}/{name}.')
    kubernetes.config.load_incluster_config()
    kube_client = kubernetes.client.ApiClient()

@kopf.on.create("neondeployments")
def create_deployment(spec, name, namespace,**_):
    kopf.info(spec,reason='CreatingDeployment',message=f'Creating {namespace}/{name}.')
    kubernetes.config.load_incluster_config()
    kube_client = kubernetes.client.ApiClient()
    aws_access_key_id = spec.get('storageConfig').get('credentials').get('awsAccessKeyID')
    aws_secret_access_key = spec.get('storageConfig').get('credentials').get('awsSecretAccessKey')

    if aws_access_key_id is None or aws_secret_access_key is None:
        raise kopf.PermanentError(f"Storage credentials are missing for NeonDeployment {namespace}/{name}")

    # Preassign resource requests and limits
    compute_node_resources = spec.get('computeNode').get('resources')
    if compute_node_resources is None:
        compute_node_resources = default_resource_limits()
    
    storage_broker_resources = spec.get('storageBroker').get('resources')
    if storage_broker_resources is None:
        storage_broker_resources = default_resource_limits()
    
    control_plane_resources = spec.get('controlPlane').get('resources')
    if control_plane_resources is None:
        control_plane_resources = default_resource_limits()

    pageserver_resources = spec.get('pageServer').get('resources')
    if pageserver_resources is None:
        pageserver_resources = default_resource_limits()

    safekeeper_resources = spec.get('safeKeeper').get('resources')
    if safekeeper_resources is None:
        safekeeper_resources = default_resource_limits()

    # Storage Configuration
    remote_storage_bucket_endpoint = spec.get('storageConfig').get('endpoint')
    remote_storage_bucket_name = spec.get('storageConfig').get('bucketName')
    remote_storage_bucket_region = spec.get('storageConfig').get('bucketRegion')
    remote_storage_prefix_in_bucket = spec.get('storageConfig').get('prefixInBucket')

    # All of the above must be present
    if remote_storage_bucket_endpoint is None or remote_storage_bucket_name is None or remote_storage_bucket_region is None or remote_storage_prefix_in_bucket is None:
        raise kopf.PermanentError(f"Storage configuration is missing for NeonDeployment {namespace}/{name}")

    try:
        # Deploy the storage credentials secret
        resources.common.deploy_secret(kube_client, namespace, aws_access_key_id, aws_secret_access_key)
        # Deploy the storage broker
        resources.storage_broker.deploy_storage_broker(kube_client, namespace)
        # Deploy the safekeeper
        resources.safekeeper.deploy_safekeeper(kube_client, namespace, safekeeper_resources,
                                                remote_storage_bucket_endpoint,
                                                remote_storage_bucket_name,
                                                remote_storage_bucket_region,
                                                remote_storage_prefix_in_bucket)
        # Deploy the control plane
        resources.control_plane.deploy_control_plane(kube_client, namespace, control_plane_resources)
        # Deploy the pageserver
        resources.pageserver.deploy_pageserver(kube_client, namespace, pageserver_resources,
                                                remote_storage_bucket_endpoint, remote_storage_bucket_name, 
                                                remote_storage_bucket_region, remote_storage_prefix_in_bucket)
        # Deploy the compute nodes
        resources.compute_node.deploy_compute_node(kube_client, namespace, compute_node_resources)
    except Exception as e:
        raise kopf.PermanentError(f"Failed to create NeonDeployment {namespace}/{name}: {e}")




@kopf.on.update("neondeployments")
def update_deployment(spec, name, namespace, **_):
    kopf.info(spec,reason='UpdatingDeployment',message=f'Updating {namespace}/{name}.')
    kubernetes.config.load_incluster_config()
    kube_client = kubernetes.client.ApiClient()
    aws_access_key_id = spec.get('storageConfig').get('credentials').get('awsAccessKeyID')
    aws_secret_access_key = spec.get('storageConfig').get('credentials').get('awsSecretAccessKey')

    if aws_access_key_id is None or aws_secret_access_key is None:
        raise kopf.PermanentError(f"Storage credentials are missing for NeonDeployment {namespace}/{name}")

    # Preassign resource requests and limits
    compute_node_resources = spec.get('computeNode').get('resources')
    if compute_node_resources is None:
        compute_node_resources = default_resource_limits()

    storage_broker_resources = spec.get('storageBroker').get('resources')
    if storage_broker_resources is None:
        storage_broker_resources = default_resource_limits()

    control_plane_resources = spec.get('controlPlane').get('resources')
    if control_plane_resources is None:
        control_plane_resources = default_resource_limits()

    pageserver_resources = spec.get('pageServer').get('resources')
    if pageserver_resources is None:
        pageserver_resources = default_resource_limits()

    safekeeper_resources = spec.get('safeKeeper').get('resources')
    if safekeeper_resources is None:
        safekeeper_resources = default_resource_limits()

    # Storage Configuration
    remote_storage_bucket_endpoint = spec.get('storageConfig').get('endpoint')
    remote_storage_bucket_name = spec.get('storageConfig').get('bucketName')
    remote_storage_bucket_region = spec.get('storageConfig').get('bucketRegion')
    remote_storage_prefix_in_bucket = spec.get('storageConfig').get('prefixInBucket')
    # All of the above must be present
    if remote_storage_bucket_endpoint is None or remote_storage_bucket_name is None or remote_storage_bucket_region is None or remote_storage_prefix_in_bucket is None:
        raise kopf.PermanentError(f"Storage configuration is missing for NeonDeployment {namespace}/{name}")
    
    try:
        # Update the storage credentials secret
        resources.common.update_secret(kube_client, namespace, aws_access_key_id, aws_secret_access_key)
        # Update the storage broker
        resources.storage_broker.update_storage_broker(kube_client, namespace)
        # Update the safekeeper
        resources.safekeeper.update_safekeeper(kube_client, namespace, safekeeper_resources,
                                                remote_storage_bucket_endpoint,
                                                remote_storage_bucket_name,
                                                remote_storage_bucket_region,
                                                remote_storage_prefix_in_bucket
                                                )
        # Update the control plane
        resources.control_plane.update_control_plane(kube_client, namespace, control_plane_resources)
        # Update the pageserver
        resources.pageserver.update_pageserver(kube_client, namespace, pageserver_resources)
        # Update the compute nodes
        resources.compute_node.update_compute_node(kube_client, namespace, compute_node_resources)
    except Exception as e:
        raise kopf.PermanentError(f"Failed to update NeonDeployment {namespace}/{name}: {e}")

@kopf.on.delete("neondeployments")
def delete_deployment(spec, name, namespace,**_):
    kopf.info(spec,reason='DeletingDeployment',message=f'Deleting {namespace}/{name}.')
    # We delete all the deployments and services
    kubernetes.config.load_incluster_config()
    kube_client = kubernetes.client.ApiClient()
    # Delete the compute nodes
    resources.compute_node.delete_compute_node(kube_client, namespace)
    # Delete the pageserver
    resources.pageserver.delete_pageserver(kube_client, namespace)
    # Delete the control plane
    resources.control_plane.delete_control_plane(kube_client, namespace)
    # Delete the safekeeper
    resources.safekeeper.delete_safekeeper(kube_client, namespace)
    # Delete the storage broker
    resources.storage_broker.delete_storage_broker(kube_client, namespace)
    # Delete the storage credentials secret
    resources.common.delete_secret(kube_client, namespace)


@kopf.on.login()
def login(**kwargs):
    return kopf.login_with_service_account(**kwargs) or kopf.login_with_kubeconfig(**kwargs)


@kopf.on.cleanup()
async def cleanup_fn(logger, **kwargs):
    logger.info("Cleanup completed.")
    pass

def check_for_pageserver(kube_client, namespace, name):
    pageserver_statefulset = kubernetes.client.AppsV1Api(kube_client).read_namespaced_stateful_set(name="pageserver", namespace=namespace)
    if pageserver_statefulset is None:
        raise kopf.PermanentError(f"Pageserver statefulset is missing for NeonTimeline {namespace}/{name}")
    if pageserver_statefulset['status']['ready_replicas'] is None:
        raise kopf.PermanentError(f"Pageserver statefulset is not ready for NeonTimeline {namespace}/{name}")
    pageserver_svc = kubernetes.client.CoreV1Api(kube_client).read_namespaced_service(name="pageserver", namespace=namespace)
    if pageserver_svc is None:
        raise kopf.PermanentError(f"Pageserver service is missing for NeonTimeline {namespace}/{name}")