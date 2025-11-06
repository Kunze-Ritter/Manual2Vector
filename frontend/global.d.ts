declare module '@playwright/test';
declare module './mocks/server' {
  export const server: any;
}
// MSW module declarations (fallback if types not resolved)
declare module 'msw' {
  export const rest: any;
  export const setupServer: any;
}
declare module 'msw/node' {
  export const setupServer: any;
}
// Vitest globals (fallback)
declare module 'vitest' {
  export const beforeAll: any;
  export const afterEach: any;
  export const afterAll: any;
  export const describe: any;
  export const test: any;
  export const expect: any;
}
// Node.js process global
declare const process: {
  env: {
    [key: string]: string | undefined;
    ADMIN_USERNAME?: string;
    ADMIN_PASSWORD?: string;
    EDITOR_USERNAME?: string;
    EDITOR_PASSWORD?: string;
    VIEWER_USERNAME?: string;
    VIEWER_PASSWORD?: string;
    API_URL?: string;
    CI?: string;
  };
};

