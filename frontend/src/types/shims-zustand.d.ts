declare module "zustand" {
  export function create<T = any>(): (initializer: any) => any;
  export type SetState<T> = (
    partial: Partial<T> | ((state: T) => Partial<T>),
    replace?: boolean,
    name?: string,
  ) => void;
}

declare module "zustand/middleware" {
  export function devtools<T = any>(fn: any, opts?: any): any;
}
