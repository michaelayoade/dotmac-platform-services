/**
 * @dotmac/graphql-client
 *
 * GraphQL client for DotMac Platform Services
 */

// Client
export {
  DotMacGraphQLClient,
  createGraphQLClient,
  getDefaultGraphQLClient,
  setDefaultGraphQLClient,
  type GraphQLClientConfig,
} from './client';

// Provider
export {
  GraphQLProvider,
  useGraphQLClient,
  useApolloClient,
} from './provider';

// Hooks
export {
  useGraphQLHealth,
  useGraphQLHealthCheck,
  type GraphQLHealthStatus,
  type UseGraphQLHealthOptions,
} from './hooks/useGraphQLHealth';

// Generated types and hooks will be exported from here after codegen
// export * from './generated/graphql';