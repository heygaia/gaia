declare module "zustand" {
  export function create<T>(
    initializer: (set: SetState<T>, get: () => T) => T,
  ): (selector?: (state: T) => unknown) => T;

  export type SetState<T> = (
    partial: Partial<T> | ((state: T) => Partial<T>),
    replace?: boolean,
    name?: string,
  ) => void;
}

declare module "zustand/middleware" {
  export function devtools<T>(
    fn: (
      set: (
        partial: Partial<T> | ((state: T) => Partial<T>),
        replace?: boolean,
      ) => void,
      get: () => T,
    ) => T,
    opts?: { name?: string },
  ): (
    set: (
      partial: Partial<T> | ((state: T) => Partial<T>),
      replace?: boolean,
    ) => void,
    get: () => T,
  ) => T;
}
