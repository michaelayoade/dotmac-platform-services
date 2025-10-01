function createClient() {
  const client = {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
    enableAuth: jest.fn(() => client),
  };

  return client;
}

module.exports = {
  createHttpClient: jest.fn(() => createClient()),
  httpClient: createClient(),
  useApiQuery: jest.fn(() => ({
    data: null,
    isLoading: false,
    error: null,
  })),
};
