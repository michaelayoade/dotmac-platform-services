/**
 * Apollo GraphQL client configuration for DotMac Platform Services
 */

import {
  ApolloClient,
  InMemoryCache,
  HttpLink,
  split,
  from,
  ApolloLink,
} from '@apollo/client';
import { getMainDefinition } from '@apollo/client/utilities';
import { GraphQLWsLink } from '@apollo/client/link/subscriptions';
import { createClient } from 'graphql-ws';
import { setContext } from '@apollo/client/link/context';
import { onError } from '@apollo/client/link/error';

export interface GraphQLClientConfig {
  httpUri?: string;
  wsUri?: string;
  getAuthToken?: () => string | null | Promise<string | null>;
  onError?: (error: any) => void;
  enableSubscriptions?: boolean;
  cache?: InMemoryCache;
}

export class DotMacGraphQLClient {
  private client: ApolloClient<any>;

  constructor(config: GraphQLClientConfig = {}) {
    const {
      httpUri = 'http://localhost:8000/graphql',
      wsUri = 'ws://localhost:8000/graphql',
      getAuthToken,
      onError: onErrorCallback,
      enableSubscriptions = true,
      cache,
    } = config;

    // HTTP Link for queries and mutations
    const httpLink = new HttpLink({
      uri: httpUri,
    });

    // WebSocket Link for subscriptions
    const wsLink = enableSubscriptions
      ? new GraphQLWsLink(
          createClient({
            url: wsUri,
            connectionParams: async () => {
              const token = await getAuthToken?.();
              return token ? { Authorization: `Bearer ${token}` } : {};
            },
          })
        )
      : null;

    // Auth link to add Authorization header
    const authLink = setContext(async (_, { headers }) => {
      const token = await getAuthToken?.();
      return {
        headers: {
          ...headers,
          ...(token && { Authorization: `Bearer ${token}` }),
        },
      };
    });

    // Error handling link
    const errorLink = onError(({ graphQLErrors, networkError, operation, forward }) => {
      if (graphQLErrors) {
        graphQLErrors.forEach(({ message, locations, path }) => {
          console.error(
            `GraphQL error: Message: ${message}, Location: ${locations}, Path: ${path}`
          );
        });
      }

      if (networkError) {
        console.error(`Network error: ${networkError}`);

        // Handle authentication errors
        if ('statusCode' in networkError && networkError.statusCode === 401) {
          // Token expired or invalid - could trigger re-authentication
          onErrorCallback?.(networkError);
        }
      }
    });

    // Combine links
    let link: ApolloLink = from([errorLink, authLink, httpLink]);

    // Split link for subscriptions vs queries/mutations
    if (wsLink) {
      link = split(
        ({ query }) => {
          const definition = getMainDefinition(query);
          return (
            definition.kind === 'OperationDefinition' &&
            definition.operation === 'subscription'
          );
        },
        wsLink,
        link
      );
    }

    this.client = new ApolloClient({
      link,
      cache: cache || new InMemoryCache({
        typePolicies: {
          Query: {
            fields: {
              // Pagination for connections
              auditEvents: {
                keyArgs: ['filter'],
                merge(existing, incoming, { args }) {
                  if (args?.after) {
                    // Append new results for pagination
                    return {
                      ...incoming,
                      nodes: [...(existing?.nodes || []), ...incoming.nodes],
                    };
                  }
                  return incoming;
                },
              },
              featureFlags: {
                keyArgs: ['filter'],
                merge(existing, incoming, { args }) {
                  if (args?.after) {
                    return {
                      ...incoming,
                      nodes: [...(existing?.nodes || []), ...incoming.nodes],
                    };
                  }
                  return incoming;
                },
              },
              services: {
                keyArgs: ['status'],
                merge(existing, incoming, { args }) {
                  if (args?.after) {
                    return {
                      ...incoming,
                      nodes: [...(existing?.nodes || []), ...incoming.nodes],
                    };
                  }
                  return incoming;
                },
              },
            },
          },
          // Cache individual items by ID
          User: {
            keyFields: ['id'],
          },
          FeatureFlag: {
            keyFields: ['key'],
          },
          AuditEvent: {
            keyFields: ['id'],
          },
          ServiceInstance: {
            keyFields: ['id'],
          },
          APIKey: {
            keyFields: ['id'],
          },
        },
      }),
      defaultOptions: {
        watchQuery: {
          errorPolicy: 'all',
          fetchPolicy: 'cache-and-network',
        },
        query: {
          errorPolicy: 'all',
          fetchPolicy: 'cache-first',
        },
      },
    });
  }

  getClient() {
    return this.client;
  }

  // Utility methods
  async clearCache() {
    await this.client.clearStore();
  }

  async refetchQueries(queries?: string[]) {
    await this.client.refetchQueries({
      include: queries || 'active',
    });
  }

  // Health check
  async healthCheck(): Promise<boolean> {
    try {
      const result = await this.client.query({
        query: require('./queries/health.graphql').HEALTH_QUERY,
        fetchPolicy: 'network-only',
      });
      return result.data?.health?.status === 'ok';
    } catch (error) {
      console.error('GraphQL health check failed:', error);
      return false;
    }
  }
}

// Default instance
let defaultClient: DotMacGraphQLClient | null = null;

export function createGraphQLClient(config?: GraphQLClientConfig): DotMacGraphQLClient {
  return new DotMacGraphQLClient(config);
}

export function getDefaultGraphQLClient(): DotMacGraphQLClient {
  if (!defaultClient) {
    defaultClient = new DotMacGraphQLClient();
  }
  return defaultClient;
}

export function setDefaultGraphQLClient(client: DotMacGraphQLClient) {
  defaultClient = client;
}