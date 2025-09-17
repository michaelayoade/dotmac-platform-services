module.exports = {
  createHttpClient: jest.fn(() => ({
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
  })),
  httpClient: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
  },
  useApiQuery: jest.fn(() => ({
    data: null,
    isLoading: false,
    error: null,
  })),
}