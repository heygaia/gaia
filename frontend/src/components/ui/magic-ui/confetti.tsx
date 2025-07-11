"use client";

import type {
  CreateTypes as ConfettiInstance,
  GlobalOptions as ConfettiGlobalOptions,
  Options as ConfettiOptions,
} from "canvas-confetti";
import confetti from "canvas-confetti";
import type { ReactNode } from "react";
import React, {
  createContext,
  forwardRef,
  useCallback,
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
} from "react";

type Api = {
  fire: (options?: ConfettiOptions) => void;
};

type Props = React.ComponentPropsWithRef<"canvas"> & {
  options?: ConfettiOptions;
  globalOptions?: ConfettiGlobalOptions;
  manualstart?: boolean;
  children?: ReactNode;
};

export type ConfettiRef = Api | null;

const ConfettiContext = createContext<Api>({} as Api);

const Confetti = forwardRef<ConfettiRef, Props>((props, ref) => {
  const {
    options,
    globalOptions = { resize: true, useWorker: true },
    manualstart = false,
    children,
    ...rest
  } = props;
  const instanceRef = useRef<ConfettiInstance | null>(null); // confetti instance

  const canvasRef = useCallback(
    // https://react.dev/reference/react-dom/components/common#ref-callback
    // https://reactjs.org/docs/refs-and-the-dom.html#callback-refs
    (node: HTMLCanvasElement) => {
      if (node !== null) {
        // <canvas> is mounted => create the confetti instance
        if (instanceRef.current) return; // if not already created
        instanceRef.current = confetti.create(node, {
          ...globalOptions,
          resize: true,
        });
      } else {
        // <canvas> is unmounted => reset and destroy instanceRef
        if (instanceRef.current) {
          instanceRef.current.reset();
          instanceRef.current = null;
        }
      }
    },
    [globalOptions],
  );

  // `fire` is a function that calls the instance() with `opts` merged with `options`
  const fire = useCallback(
    (opts = {}) => instanceRef.current?.({ ...options, ...opts }),
    [options],
  );

  const api = useMemo(
    () => ({
      fire,
    }),
    [fire],
  );

  useImperativeHandle(ref, () => api, [api]);

  useEffect(() => {
    if (!manualstart) {
      fire();
    }
  }, [manualstart, fire]);

  return (
    <ConfettiContext.Provider value={api}>
      <canvas ref={canvasRef} {...rest} />
      {children}
    </ConfettiContext.Provider>
  );
});

Confetti.displayName = "Confetti";

export { Confetti };

// export function ConfettiFireworks({
//   color,
//   children,
//   onPress,
//   endContent,
//   props,
//   handleKeyDown,
// }: any) {
// const handleClick = () => {
// const duration = 5 * 1000;
// const animationEnd = Date.now() + duration;
// const defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 1 };

// const randomInRange = (min: number, max: number) =>
//   Math.random() * (max - min) + min;

// const interval = window.setInterval(() => {
//   const timeLeft = animationEnd - Date.now();

//   if (timeLeft <= 0) {
//     return clearInterval(interval);
//   }

//   const particleCount = 50 * (timeLeft / duration);
//   confetti({
//     ...defaults,
//     particleCount,
//     origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 },
//   });
//   confetti({
//     ...defaults,
//     particleCount,
//     origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 },
//   });
// }, 250);

// onPress();
// };

//   return (
//     <div className="relative">
//       <Button
//         onPress={onPress}
//         color={color}
//         endContent={endContent}
//         type="submit"
//         onKeyDown={handleKeyDown}
//         {...props}
//       >
//         {children}
//       </Button>
//     </div>
//   );
// }

export default Confetti;
