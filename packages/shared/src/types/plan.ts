export type PlanAction = 'deploy' | 'rollback' | 'test' | 'build';

export interface DeploymentPlan {
    id: string;
    action: PlanAction;
    version?: string;
    environments: string[];
    postSteps: string[];
    warnings?: string[];
    status:
    | 'pending_approval'
    | 'approved'
    | 'running'
    | 'failed'
    | 'rolled_back'
    | 'succeeded';
    createdAt: string; // ISO timestamp
    updatedAt: string; // ISO timestamp
}
