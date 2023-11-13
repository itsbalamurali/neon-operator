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
    name: str
    value: Optional[str] = None
    vartype: str


class ExtensionData(BaseModel):
    control_data: Dict[str, str]
    archive_path: str


class RemoteExtensionSpec(BaseModel):
    public_extensions: Optional[List[str]] = None
    custom_extensions: Optional[List[str]] = None
    library_index: Dict[str, str]
    extension_data: Dict[str, ExtensionData]


class Role(BaseModel):
    name: str
    encrypted_password: Optional[str] = None
    replication: Optional[bool] = None
    bypassrls: Optional[bool] = None
    options: Optional[List[GenericOption]] = None


class Database(BaseModel):
    name: str
    owner: str
    options: Optional[List[GenericOption]] = None
    restrict_conn: bool = False
    invalid: bool = False


class Cluster(BaseModel):
    cluster_id: Optional[str] = None
    name: Optional[str] = None
    state: Optional[str] = None
    roles: List[Role]
    databases: List[Database]
    postgresql_conf: Optional[str] = None
    settings: List[GenericOption]


class DeltaOperation(BaseModel):
    action: str
    name: str
    new_name: Optional[str] = None


class ComputeMode(Enum):
    primary = "Primary"
    replica = "Replica"
    static = "Static"


class ComputeSpec(BaseModel):
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
    Empty = "empty"
    Attached = "attached"


class ControlPlaneSpecResponse(BaseModel):
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
    tenants: List[ValidateResponseTenant]


class AttachHookRequest(BaseModel):
    tenant_id: str
    node_id: str


class AttachHookResponse(BaseModel):
    gen: int


@app.get("/")
def read_root():
    return {"message": "Control Panel API is running"}


@app.post("/re-attach")
def re_attach(request: ReAttachRequest):
    tenants = []
    tenants.append(ReAttachResponseTenant(id=request.node_id, gen=1))
    response = ReAttachResponse(tenants=tenants)
    return response


@app.post("/validate")
def validate(request: ValidateRequest):
    tenants = []
    for tenant in request.tenants:
        # TODO: get tenant from k8s resources
        k8s_tenant = None
        valid = tenant.gen == k8s_tenant.gen
        tenants.append(ValidateResponseTenant(id=tenant.id, valid=valid))
    response = ValidateResponse(tenants=tenants)
    return response


@app.post("/attach-hook")
def attach_hook(request: AttachHookRequest):
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
