import os
from enum import Enum
from typing import Optional, List, Dict

import uvicorn
from fastapi import FastAPI
from fastapi.security import HTTPBearer
from pydantic import BaseModel

oauth2_scheme = HTTPBearer()

app = FastAPI()


class GenericOption(BaseModel):
    """
    Represents a generic option with a name, value, and type.

    Attributes:
        name (str): The name of the option.
        value (Optional[str]): The value of the option. Defaults to None.
        vartype (str): The type of the option.
    """
    name: str
    value: Optional[str] = None
    vartype: str


class ExtensionData(BaseModel):
    """
    Data model for extension data.

    Attributes:
        control_data (Dict[str, str]): A dictionary containing control data.
        archive_path (str): The path to the archive.
    """
    control_data: Dict[str, str]
    archive_path: str


class RemoteExtensionSpec(BaseModel):
    """
    Represents the specification for remote extensions.

    Attributes:
    public_extensions: Optional[List[str]]
        List of public extensions.
    custom_extensions: Optional[List[str]]
        List of custom extensions.
    library_index: Dict[str, str]
        Dictionary containing the library index.
    extension_data: Dict[str, ExtensionData]
        Dictionary containing the extension data.
    """
    public_extensions: Optional[List[str]] = None
    custom_extensions: Optional[List[str]] = None
    library_index: Dict[str, str]
    extension_data: Dict[str, ExtensionData]


class Role(BaseModel):
    """
    Represents a role in the system.

    Attributes:
        name (str): The name of the role.
        encrypted_password (Optional[str]): The encrypted password for the role.
        replication (Optional[bool]): Whether the role should be replicated.
        bypassrls (Optional[bool]): Whether the role should bypass RLS.
        options (Optional[List[GenericOption]]): A list of generic options for the role.
    """
    name: str
    encrypted_password: Optional[str] = None
    replication: Optional[bool] = None
    bypassrls: Optional[bool] = None
    options: Optional[List[GenericOption]] = None


class Database(BaseModel):
    """
    Represents a database object with a name, owner, and optional list of options.
    """
    name: str
    owner: str
    options: Optional[List[GenericOption]] = None
    restrict_conn: bool = False
    invalid: bool = False


class Cluster(BaseModel):
    """
    Represents a cluster in the system.

    Attributes:
        cluster_id (str, optional): The ID of the cluster.
        name (str, optional): The name of the cluster.
        state (str, optional): The state of the cluster.
        roles (List[Role]): The roles assigned to the cluster.
        databases (List[Database]): The databases associated with the cluster.
        postgresql_conf (str, optional): The PostgreSQL configuration for the cluster.
        settings (List[GenericOption]): The generic options for the cluster.
    """
    cluster_id: Optional[str] = None
    name: Optional[str] = None
    state: Optional[str] = None
    roles: List[Role]
    databases: List[Database]
    postgresql_conf: Optional[str] = None
    settings: List[GenericOption]


class DeltaOperation(BaseModel):
    """
    Represents a delta operation that can be performed on a resource.

    Attributes:
        action (str): The action to be performed on the resource.
        name (str): The name of the resource.
        new_name (Optional[str], optional): The new name of the resource, if applicable.
    """
    action: str
    name: str
    new_name: Optional[str] = None

class ComputeMode(Enum):
    """
    An enumeration representing the different compute modes.

    Attributes:
        primary (str): Represents the primary compute mode.
        replica (str): Represents the replica compute mode.
        static (str): Represents the static compute mode.
    """
    primary = "Primary"
    replica = "Replica"
    static = "Static"


class ComputeSpec(BaseModel):
    """
    Represents the specification for a compute operation.

    Attributes:
        format_version (float): The version of the compute specification format.
        operation_uuid (Optional[str]): The UUID of the compute operation.
        cluster (Cluster): The cluster on which the compute operation is to be performed.
        delta_operations (Optional[List[DeltaOperation]]): The list of delta operations to be applied.
        skip_pg_catalog_updates (bool): Whether to skip updates to the pg_catalog table.
        tenant_id (str): The ID of the tenant for which the compute operation is being performed.
        timeline_id (str): The ID of the timeline for which the compute operation is being performed.
        pageserver_connstring (str): The connection string for the page server.
        safekeeper_connstrings (List[str]): The list of connection strings for the safekeepers.
        mode (Optional[ComputeMode]): The mode in which the compute operation is to be performed.
        storage_auth_token (Optional[str]): The authentication token for the storage system.
        remote_extensions (Optional[List[RemoteExtensionSpec]]): The list of remote extensions to be applied.
    """
    format_version: float
    operation_uuid: Optional[str] = None
    cluster: Cluster
    delta_operations: Optional[List[DeltaOperation]] = None
    skip_pg_catalog_updates: bool = True
    tenant_id: str
    timeline_id: str
    pageserver_connstring: str
    safekeeper_connstrings: List[str]
    mode: Optional[ComputeMode] = None
    storage_auth_token: Optional[str] = None
    remote_extensions: Optional[List[RemoteExtensionSpec]] = None


class ControlPlaneComputeStatus(Enum):
    """
    Enum class representing the status of a control plane compute instance.
    """
    Empty = "empty"
    Attached = "attached"


class ControlPlaneSpecResponse(BaseModel):
    """
    Represents the response for the control plane spec.

    Attributes:
        spec (ComputeSpec): The compute spec.
        status (ControlPlaneComputeStatus): The control plane compute status.
    """
    spec: ComputeSpec
    status: ControlPlaneComputeStatus


class ReAttachRequest(BaseModel):
    node_id: str


class ReAttachResponseTenant(BaseModel):
    id: str
    gen: int


class ReAttachResponse(BaseModel):
    tenants: List[ReAttachResponseTenant]


class ValidateRequestTenant(BaseModel):
    id: str
    gen: int


class ValidateRequest(BaseModel):
    tenants: List[ValidateRequestTenant]


class ValidateResponseTenant(BaseModel):
    id: str
    valid: bool


class ValidateResponse(BaseModel):
    """
    Represents the response returned by the validation API endpoint.

    Attributes:
        tenants (List[ValidateResponseTenant]): A list of tenants containing the validation results.
    """
    tenants: List[ValidateResponseTenant]


class AttachHookRequest(BaseModel):
    """
    Represents a request to attach a hook to a node.

    Args:
        tenant_id (str): The ID of the tenant.
        node_id (str): The ID of the node to attach the hook to.
    """
    tenant_id: str
    node_id: str


class AttachHookResponse(BaseModel):
    """
    Represents the response returned by the attach hook API endpoint.

    Attributes:
        gen (int): The generation number of the hook.
    """
    gen: int


class WelcomeMessage(BaseModel):
    message: str


@app.get("/")
def read_root() -> WelcomeMessage:
    return WelcomeMessage(message="Control Panel API is running")


@app.post("/re-attach")
def re_attach(re_attach_request: ReAttachRequest) -> ReAttachResponse:
    """
    Re-attach is called to re-attach a tenant to a page server to aqcuire a new generation number.
    """
    print(f"Re-attaching pageserver node: {re_attach_request.node_id}")
    tenants = []
    tenants.append(ReAttachResponseTenant(id=re_attach_request.node_id, gen=1))
    response = ReAttachResponse(tenants=tenants)
    return response


@app.post("/validate")
def validate(validate_request: ValidateRequest) -> ValidateResponse:
    """
    Validate is called to validate the tenant generation numbers.
    """
    tenants = []
    for tenant in validate_request.tenants:
        # TODO: get tenant from k8s resources
        k8s_tenant = None
        valid = tenant.gen == k8s_tenant.gen
        tenants.append(ValidateResponseTenant(id=tenant.id, valid=valid))
    response = ValidateResponse(tenants=tenants)
    return response


@app.post("/attach-hook")
def attach_hook(request: AttachHookRequest) -> AttachHookResponse:
    """
    Attach hook is called to attach a tenant to a page server to aqcuire a new generation number.
    """
    tenant_state = None  # TODO: get tenant_state from k8s resource
    # Check if tenant exists with tenant id i.e. request.tenant_id if not create it with gen=0 with page server id
    # i.e. request.node_id and save it
    if request.node_id != "":
        print(f'tenant_id: {request.tenant_id}, ps_id: {request.node_id}, generation: 1, issuing')
    elif tenant_state.pageserver != "":
        print(
            f'tenant_id: {request.tenant_id}, ps_id: {tenant_state.pageserver}, generation: {tenant_state.generation}, dropping')
    else:
        print(f'tenant_id: {request.tenant_id}, no-op: tenant already has no pageserver')

    response = AttachHookResponse(gen=1)
    return response


@app.get("/compute/api/v2/computes/{compute_id}/spec")
def get_compute_spec(compute_id: str) -> ControlPlaneSpecResponse:
    """
    Get compute spec is called to get the compute spec for a given compute_id
    """
    print(f"Getting compute spec for compute_id: {compute_id}")
    namespace = os.getenv("NAMESPACE")
    # TODO: get the compute deployment from k8s using compute_id
    # Dummy values to get the compute-node pods running
    response = ControlPlaneSpecResponse(
        spec=ComputeSpec(
            format_version=1.0,
            tenant_id="9ef87a5bf0d92544f6fafeeb3239695c",
            timeline_id="de200bd42b49cc1814412c7e592dd6e9",
            cluster=Cluster(
                roles=[
                    Role(
                        name="postgres"
                    )
                ],
                databases=[
                    Database(
                        name="testdatabase",
                        owner="postgres"
                    )
                ],
                settings=[
                    GenericOption(
                        name="fsync",
                        value="off",
                        vartype="bool"
                    ),
                    GenericOption(
                        name="wal_level",
                        value="logical",
                        vartype="enum"
                    ),
                    GenericOption(
                        name="wal_log_hints",
                        value="on",
                        vartype="bool"
                    ),
                    GenericOption(
                        name="log_connections",
                        value="on",
                        vartype="bool"
                    ),
                    GenericOption(
                        name="port",
                        value="55433",
                        vartype="integer"
                    ),
                    GenericOption(
                        name="shared_buffers",
                        value="1MB",
                        vartype="string"
                    ),
                    GenericOption(
                        name="max_connections",
                        value="100",
                        vartype="integer"
                    ),
                    GenericOption(
                        name="listen_addresses",
                        value="0.0.0.0",
                        vartype="string"
                    ),
                    GenericOption(
                        name="max_wal_senders",
                        value="10",
                        vartype="integer"
                    ),
                    GenericOption(
                        name="max_replication_slots",
                        value="10",
                        vartype="integer"
                    ),
                    GenericOption(
                        name="wal_sender_timeout",
                        value="5s",
                        vartype="string"
                    ),
                    GenericOption(
                        name="wal_keep_size",
                        value="0",
                        vartype="integer"
                    ),
                    GenericOption(
                        name="password_encryption",
                        value="md5",
                        vartype="enum"
                    ),
                    GenericOption(
                        name="restart_after_crash",
                        value="off",
                        vartype="bool"
                    ),
                    GenericOption(
                        name="synchronous_standby_names",
                        value="walproposer",
                        vartype="string"
                    ),
                    GenericOption(
                        name="shared_preload_libraries",
                        value="neon",
                        vartype="string"
                    ),
                    GenericOption(
                        name="max_replication_write_lag",
                        value="500MB",
                        vartype="string"
                    ),
                    GenericOption(
                        name="max_replication_flush_lag",
                        value="10GB",
                        vartype="string"
                    ),
                ]
            ),
            skip_pg_catalog_updates=False,
            pageserver_connstring=f"host=pageserver.{namespace}.svc.cluster.local port=6400",
            safekeeper_connstrings=[
                f"safekeeper-0.safekeeper.{namespace}.svc.cluster.local:5454",
                f"safekeeper-1.safekeeper.{namespace}.svc.cluster.local:5454",
                f"safekeeper-2.safekeeper.{namespace}.svc.cluster.local:5454"
            ],
            mode=ComputeMode.primary,
        ),
        status=ControlPlaneComputeStatus.Empty
    )
    return response


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=1234)
