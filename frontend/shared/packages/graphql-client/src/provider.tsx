/**
 * Apollo GraphQL Provider for DotMac Platform Services
 */

import React, { createContext, useContext, ReactNode } from 'react';
import { ApolloProvider } from '@apollo/client';
import { DotMacGraphQLClient, GraphQLClientConfig } from './client';

interface GraphQLProviderContextValue {
  client: DotMacGraphQLClient;
  config: GraphQLClientConfig;
}

const GraphQLProviderContext = createContext<GraphQLProviderContextValue | null>(null);

interface GraphQLProviderProps {
  children: ReactNode;
  config?: GraphQLClientConfig;
  client?: DotMacGraphQLClient;
}

export function GraphQLProvider({ children, config = {}, client }: GraphQLProviderProps) {
  const graphqlClient = client || new DotMacGraphQLClient(config);
  const apolloClient = graphqlClient.getClient();

  const contextValue: GraphQLProviderContextValue = {
    client: graphqlClient,
    config,
  };

  return (
    <GraphQLProviderContext.Provider value={contextValue}>
      <ApolloProvider client={apolloClient}>
        {children}
      </ApolloProvider>
    </GraphQLProviderContext.Provider>
  );
}

export function useGraphQLClient(): GraphQLProviderContextValue {
  const context = useContext(GraphQLProviderContext);
  if (!context) {
    throw new Error('useGraphQLClient must be used within a GraphQLProvider');
  }
  return context;
}

// Convenience hook to get the Apollo client directly
export function useApolloClient() {
  const { client } = useGraphQLClient();
  return client.getClient();
}