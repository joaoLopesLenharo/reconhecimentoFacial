/**
 * Configuração global para Jest
 */

// Importa matchers customizados do testing-library
import '@testing-library/jest-dom';

// Mock global do console para evitar logs desnecessários durante os testes
global.console = {
    ...console,
    // Mantém apenas os logs de erro durante os testes
    log: jest.fn(),
    debug: jest.fn(),
    info: jest.fn(),
    warn: jest.fn(),
    error: console.error
};

// Mock do localStorage
const localStorageMock = {
    getItem: jest.fn(),
    setItem: jest.fn(),
    removeItem: jest.fn(),
    clear: jest.fn(),
};
global.localStorage = localStorageMock;

// Mock do sessionStorage
const sessionStorageMock = {
    getItem: jest.fn(),
    setItem: jest.fn(),
    removeItem: jest.fn(),
    clear: jest.fn(),
};
global.sessionStorage = sessionStorageMock;

// Mock do fetch
global.fetch = jest.fn();

// Mock do WebSocket/Socket.IO
global.WebSocket = jest.fn();

// Configuração para testes que envolvem timers
jest.useFakeTimers();

// Cleanup após cada teste
afterEach(() => {
    jest.clearAllMocks();
    jest.clearAllTimers();
    document.body.innerHTML = '';
    document.head.innerHTML = '';
});
