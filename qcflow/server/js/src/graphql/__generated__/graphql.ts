export type Maybe<T> = T | null;
export type InputMaybe<T> = Maybe<T>;
export type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
export type MakeOptional<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]?: Maybe<T[SubKey]> };
export type MakeMaybe<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]: Maybe<T[SubKey]> };
export type MakeEmpty<T extends { [key: string]: unknown }, K extends keyof T> = { [_ in K]?: never };
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
/** All built-in and custom scalars, mapped to their actual values */
export type Scalars = {
  ID: { input: string; output: string; }
  String: { input: string; output: string; }
  Boolean: { input: boolean; output: boolean; }
  Int: { input: number; output: number; }
  Float: { input: number; output: number; }
  /** LongString Scalar type to prevent truncation to max integer in JavaScript. */
  LongString: { input: GraphQLLongString; output: GraphQLLongString; }
};

export type QCFlowGetMetricHistoryBulkIntervalInput = {
  endStep?: InputMaybe<Scalars['Int']['input']>;
  maxResults?: InputMaybe<Scalars['Int']['input']>;
  metricKey?: InputMaybe<Scalars['String']['input']>;
  runIds?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  startStep?: InputMaybe<Scalars['Int']['input']>;
};

export type QCFlowGetRunInput = {
  runId?: InputMaybe<Scalars['String']['input']>;
  runUuid?: InputMaybe<Scalars['String']['input']>;
};

export enum QCFlowModelVersionStatus {
  FAILED_REGISTRATION = 'FAILED_REGISTRATION',
  PENDING_REGISTRATION = 'PENDING_REGISTRATION',
  READY = 'READY'
}

export enum QCFlowRunStatus {
  FAILED = 'FAILED',
  FINISHED = 'FINISHED',
  KILLED = 'KILLED',
  RUNNING = 'RUNNING',
  SCHEDULED = 'SCHEDULED'
}

export type GetRunVariables = Exact<{
  data: QCFlowGetRunInput;
}>;


export type GetRun = { qcflowGetRun: { __typename: 'QCFlowGetRunResponse', apiError: { __typename: 'ApiError', helpUrl: string | null, code: string | null, message: string | null } | null, run: { __typename: 'QCFlowRunExtension', info: { __typename: 'QCFlowRunInfo', runName: string | null, status: QCFlowRunStatus | null, runUuid: string | null, experimentId: string | null, artifactUri: string | null, endTime: GraphQLLongString | null, lifecycleStage: string | null, startTime: GraphQLLongString | null, userId: string | null } | null, experiment: { __typename: 'QCFlowExperiment', experimentId: string | null, name: string | null, artifactLocation: string | null, lifecycleStage: string | null, lastUpdateTime: GraphQLLongString | null, tags: Array<{ __typename: 'QCFlowExperimentTag', key: string | null, value: string | null }> | null } | null, modelVersions: Array<{ __typename: 'QCFlowModelVersion', status: QCFlowModelVersionStatus | null, version: string | null, name: string | null, source: string | null }> | null, data: { __typename: 'QCFlowRunData', metrics: Array<{ __typename: 'QCFlowMetric', key: string | null, value: number | null, step: GraphQLLongString | null, timestamp: GraphQLLongString | null }> | null, params: Array<{ __typename: 'QCFlowParam', key: string | null, value: string | null }> | null, tags: Array<{ __typename: 'QCFlowRunTag', key: string | null, value: string | null }> | null } | null, inputs: { __typename: 'QCFlowRunInputs', datasetInputs: Array<{ __typename: 'QCFlowDatasetInput', dataset: { __typename: 'QCFlowDataset', digest: string | null, name: string | null, profile: string | null, schema: string | null, source: string | null, sourceType: string | null } | null, tags: Array<{ __typename: 'QCFlowInputTag', key: string | null, value: string | null }> | null }> | null } | null } | null } | null };

export type GetMetricHistoryBulkIntervalVariables = Exact<{
  data: QCFlowGetMetricHistoryBulkIntervalInput;
}>;


export type GetMetricHistoryBulkInterval = { qcflowGetMetricHistoryBulkInterval: { __typename: 'QCFlowGetMetricHistoryBulkIntervalResponse', metrics: Array<{ __typename: 'QCFlowMetricWithRunId', timestamp: GraphQLLongString | null, step: GraphQLLongString | null, runId: string | null, key: string | null, value: number | null }> | null, apiError: { __typename: 'ApiError', code: string | null, message: string | null } | null } | null };
