// // src/features/mail/data/mail-animation.data.ts

// import React, { useState, useEffect } from "react";
// import { Inbox, Mail, Send } from "lucide-react";
// import { AnimatePresence, motion } from "framer-motion";

// import { ComposerProvider } from "@/features/chat/contexts/ComposerContext";
// import EmailComposeSection from "@/features/chat/components/bubbles/bot/EmailComposeSection";
// import EmailThreadCard from "@/features/chat/components/bubbles/bot/EmailThreadCard";
// import EmailListCard from "@/features/mail/components/EmailListCard";
// import { EmailComposeData, EmailFetchData, EmailThreadData, } from "@/types/features/mailTypes";

// // --- MOCK DATA & CONFIGURATION ---

// const timeAgo = (hours: number): string => new Date(Date.now() - hours * 60 * 60 * 1000).toISOString();

// const composeData: EmailComposeData[] = [
//   { to: ["dhruv@heygaia.io"], subject: "Investor Meeting Inquiry", body: "Hey Dhruv,\n\nI hope you're doing well! I wanted to check in about the investor meeting. Do we have a confirmed time and agenda? Let me know if there's anything specific I should prepare.\n\nThanks!\n\nBest,\nAryan", },
// ];

// const threadData: EmailThreadData = {
//   thread_id: "198611a5949ce1d5", messages_count: 1,
//   messages: [
//     { id: "198611a5949ce1d5", from: "Product Hunt Daily <hello@digest.producthunt.com>", subject: "😸 Kicked out of YC", time: "2025-07-31 15:29", snippet: "Plus: agents, are building agents now Product Hunt Thursday, Jul 31 The Leaderboard Workflow, Locked In gm legends, happy Thursday. Here's today's lineup: Okibi lets you explain a workflow once", body: '<!DOCTYPE html><html><head><meta content="text/html; charset=UTF-8" http-equiv="Content-Type"><style>body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif,"Apple Color Emoji","Segoe UI Emoji","Segoe UI Symbol";margin:0;padding:0}</style></head><body><div style="max-width:600px;font-size:15px;margin:0 auto;padding:20px 8px"><div style="display:none;font-size:1px;height:0;width:0;opacity:0;overflow:hidden">Plus: agents, are building agents now</div><table style="width:100%;border-collapse:collapse"><tr><td style="box-sizing:border-box;width:92px;border-top-left-radius:10px;border-bottom-left-radius:10px;padding-bottom:10px;background-image:linear-gradient(#ff6154,#ff6154)" bgcolor="#ff6154" valign="bottom"><div style="padding-left:5px"><a target="_blank" href="#" style="text-decoration:none;color:black"><img alt="Product Hunt" height="80px" src="https://ph-static.imgix.net/static/glasshole_kitty_logo.png"></a></div></td><td style="box-sizing:border-box;width:500px;border-top-right-radius:10px;border-bottom-right-radius:10px;padding-bottom:20px;background-image:linear-gradient(#f9e6ce,#f9e6ce)" bgcolor="#f9e6ce" valign="bottom"><div style="padding-left:10px"><table style="width:100%;border-collapse:collapse;height:100%"><tr><td style="box-sizing:border-box" valign="bottom"><div style="color:#ff6154;font-size:16px;padding-bottom:20px">Thursday, Jul 31</div><div style="font-size:40px;font-weight:700;color:#000!important">The Leaderboard</div></td><td style="box-sizing:border-box;margin-bottom:-10px" valign="bottom"><img height="295px" width="228px" src="https://ph-static.imgix.net/static/newsletter-header-graphic.png"></td></tr></table></div></td></tr></table><div style="background-color:white;width:100%;box-sizing:border-box;padding-top:24px"><div class="title"><a target="_blank" class="title-link" href="#" style="text-decoration:none;color:#21293c;display:block;font-size:32px;font-weight:800;line-height:40px;margin-bottom:8px">Workflow, Locked In</a></div><div class="content" style="color:#21293c;font-size:14px;line-height:24px;white-space:normal;margin-bottom:16px"><p>gm legends, happy Thursday.</p><p>Here’s today’s lineup: Okibi lets you explain a workflow once and hands you an agent that just runs it; Mocha turns a description into a full stack app with auth, billing, hosting and deploy all live in minutes; GitBook’s new dynamic adaptive docs change what readers see based on context so writers stop guessing; and the founder comeback story—kicked out of YC, fought to get back in.</p></div></div></div></body></html>' }
//   ],
// };

// const initialFetchData: EmailFetchData[] = [
//     { from: "Updates <updates@vercel.com>", subject: "New Project Deployed Successfully", time: timeAgo(1) },
//     { from: "GitHub <noreply@github.com>", subject: "[hey-gaia/core] New issue created: #582", time: timeAgo(2) },
//     { from: "Linear <notifications@linear.app>", subject: "You were mentioned in an issue", time: timeAgo(25) },
//     { from: "Figma <noreply@figma.com>", subject: "Dhruv left a comment on 'Homepage V3'", time: timeAgo(28) },
// ];
// const fetchData: EmailFetchData[] = Array.from({ length: 5 }).flatMap(() => initialFetchData).map((email, index) => ({ ...email, thread_id: `thread_${index + 1}` }));

// const summaryComponent = ( <div className="prose max-w-none text-sm text-gray-300 dark:prose-invert"> <p>Here's a summary of the email from Product Hunt Daily...</p> <h3 className="mt-4 mb-2 text-base font-bold text-white">Summary</h3> <ul className="mb-4 list-disc pl-5 text-gray-400"> <li><strong>Core Message</strong>: Discusses challenges faced by founders and their journey to reapply to YC.</li> </ul> </div> );

// const mockComposerValue = { appendToInput: (text: string) => { console.log(`EmailListCard tried to append: "${text}"`); }, };

// // --- SELF-ANIMATING COMPONENTS FOR EACH STEP ---

// const ComposeAnimation = () => (
//     <motion.div
//         initial={{ opacity: 0, y: 20 }}
//         animate={{ opacity: 1, y: 0 }}
//         transition={{ duration: 0.5, ease: "easeOut" }}
//     >
//         <EmailComposeSection email_compose_data={composeData} />
//     </motion.div>
// );

// const FetchAnimation = () => {
//     const [visibleEmails, setVisibleEmails] = useState<EmailFetchData[]>([]);
//     const [isExpanded, setIsExpanded] = useState(false);

//     useEffect(() => {
//         // Expand the card first
//         const expandTimer = setTimeout(() => setIsExpanded(true), 300);

//         // Then, simulate emails fetching one by one after expansion
//         let emailTimers: NodeJS.Timeout[] = [];
//         if (isExpanded) {
//             emailTimers = fetchData.map((email, index) =>
//                 setTimeout(() => {
//                     setVisibleEmails(prev => [...prev, email]);
//                 }, index * 80) // Stagger the appearance of each email
//             );
//         }
//         return () => {
//             clearTimeout(expandTimer);
//             emailTimers.forEach(clearTimeout);
//         };
//     }, [isExpanded]); // Rerun when isExpanded becomes true

//     return (
//         <ComposerProvider value={mockComposerValue}>
//             <motion.div
//                 initial={{ opacity: 0, height: "80px" }}
//                 animate={{
//                     opacity: 1,
//                     height: isExpanded ? "auto" : "80px",
//                 }}
//                 transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
//                 className="overflow-hidden"
//             >
//                 <EmailListCard emails={visibleEmails} />
//             </motion.div>
//         </ComposerProvider>
//     );
// };

// const ViewAnimation = () => {
//     const [isExpanded, setIsExpanded] = useState(false);
//     const [showSummary, setShowSummary] = useState(false);

//     useEffect(() => {
//         const expandTimer = setTimeout(() => setIsExpanded(true), 800);
//         const summaryTimer = setTimeout(() => setShowSummary(true), 1500);

//         return () => {
//             clearTimeout(expandTimer);
//             clearTimeout(summaryTimer);
//         };
//     }, []);

//     return (
//         <div className="w-full space-y-3">
//             <motion.div
//                 key="email-thread-wrapper"
//                 initial={{ opacity: 0, y: 20 }}
//                 animate={{ opacity: 1, y: 0 }}
//                 transition={{ duration: 0.5, ease: "easeOut" }}
//             >
//                 <EmailThreadCard
//                     key={isExpanded ? "expanded" : "collapsed"}
//                     emailThreadData={threadData}
//                     isExpandedDefault={isExpanded}
//                 />
//             </motion.div>
//             <AnimatePresence>
//                 {showSummary && (
//                     <motion.div
//                         key="summary"
//                         initial={{ opacity: 0, y: 20 }}
//                         animate={{ opacity: 1, y: 0 }}
//                         exit={{ opacity: 0 }}
//                         transition={{ duration: 0.6, ease: "easeOut" }}
//                     >
//                         {summaryComponent}
//                     </motion.div>
//                 )}
//             </AnimatePresence>
//         </div>
//     );
// };

// // --- MAIN EXPORTED STEPS ---

// export const animationSteps = [
//     { name: "Compose", icon: <Send />, prompt: "Compose an email to dhruv@heygaia.io asking about the investor meeting.", component: <ComposeAnimation />, },
//     { name: "Fetch", icon: <Mail />, prompt: "Fetch my latest emails from Gmail.", component: <FetchAnimation />, },
//     { name: "View", icon: <Inbox />, prompt: "Tell me about the email from Product Hunt.", component: <ViewAnimation />, },
// ];

// src/features/mail/data/mail-animation.data.ts

// mail-animation.data.tsx
import { AnimatePresence, motion } from "framer-motion";
import { Inbox, Mail, Send } from "lucide-react";
import React, { useEffect, useRef, useState } from "react";

import EmailComposeSection from "@/features/chat/components/bubbles/bot/EmailComposeSection";
import EmailThreadCard from "@/features/chat/components/bubbles/bot/EmailThreadCard";
import EmailListCard from "@/features/mail/components/EmailListCard";
import {
  EmailComposeData,
  EmailFetchData,
  EmailThreadData,
} from "@/types/features/mailTypes";

// --- MOCK DATA & CONFIGURATION ---

const timeAgo = (hours: number): string =>
  new Date(Date.now() - hours * 60 * 60 * 1000).toISOString();

const composeData: EmailComposeData[] = [
  {
    to: ["dhruv@heygaia.io"],
    subject: "Investor Meeting Inquiry",
    body: "Hey Dhruv,\n\nI hope you're doing well! I wanted to check in about the investor meeting. Do we have a confirmed time and agenda? Let me know if there's anything specific I should prepare.\n\nThanks!\n\nBest,\nAryan",
  },
];

const threadData: EmailThreadData = {
  thread_id: "198611a5949ce1d5",
  messages_count: 1,
  messages: [
    {
      id: "198611a5949ce1d5",
      from: "Product Hunt Daily <hello@digest.producthunt.com>",
      subject: "😸 Kicked out of YC",
      time: "2025-07-31 15:29",
      snippet:
        "Plus: agents, are building agents now Product Hunt Thursday, Jul 31 The Leaderboard Workflow, Locked In gm legends, happy Thursday. Here's today's lineup: Okibi lets you explain a workflow once",
      body: '<!DOCTYPE html><html><head><meta content="text/html; charset=UTF-8" http-equiv="Content-Type"><style>body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif,"Apple Color Emoji","Segoe UI Emoji","Segoe UI Symbol";margin:0;padding:0}</style></head><body><div style="max-width:600px;font-size:15px;margin:0 auto;padding:20px 8px"><div style="display:none;font-size:1px;height:0;width:0;opacity:0;overflow:hidden">Plus: agents, are building agents now</div><table style="width:100%;border-collapse:collapse"><tr><td style="box-sizing:border-box;width:92px;border-top-left-radius:10px;border-bottom-left-radius:10px;padding-bottom:10px;background-image:linear-gradient(#ff6154,#ff6154)" bgcolor="#ff6154" valign="bottom"><div style="padding-left:5px"><a target="_blank" href="#" style="text-decoration:none;color:black"><img alt="Product Hunt" height="80px" src="https://ph-static.imgix.net/static/glasshole_kitty_logo.png"></a></div></td><td style="box-sizing:border-box;width:500px;border-top-right-radius:10px;border-bottom-right-radius:10px;padding-bottom:20px;background-image:linear-gradient(#f9e6ce,#f9e6ce)" bgcolor="#f9e6ce" valign="bottom"><div style="padding-left:10px"><table style="width:100%;border-collapse:collapse;height:100%"><tr><td style="box-sizing:border-box" valign="bottom"><div style="color:#ff6154;font-size:16px;padding-bottom:20px">Thursday, Jul 31</div><div style="font-size:40px;font-weight:700;color:#000!important">The Leaderboard</div></td><td style="box-sizing:border-box;margin-bottom:-10px" valign="bottom"><img height="295px" width="228px" src="https://ph-static.imgix.net/static/newsletter-header-graphic.png"></td></tr></table></div></td></tr></table><div style="background-color:white;width:100%;box-sizing:border-box;padding-top:24px"><div class="title"><a target="_blank" class="title-link" href="#" style="text-decoration:none;color:#21293c;display:block;font-size:32px;font-weight:800;line-height:40px;margin-bottom:8px">Workflow, Locked In</a></div><div class="content" style="color:#21293c;font-size:14px;line-height:24px;white-space:normal;margin-bottom:16px"><p>gm legends, happy Thursday.</p><p>Here’s today’s lineup: Okibi lets you explain a workflow once and hands you an agent that just runs it; Mocha turns a description into a full stack app with auth, billing, hosting and deploy all live in minutes; GitBook’s new dynamic adaptive docs change what readers see based on context so writers stop guessing; and the founder comeback story—kicked out of YC, fought to get back in.</p></div></div></div></body></html>',
    },
  ],
};

const initialFetchData: EmailFetchData[] = [
  {
    from: "Updates <updates@vercel.com>",
    subject: "New Project Deployed Successfully",
    time: timeAgo(1),
  },
  {
    from: "GitHub <noreply@github.com>",
    subject: "[hey-gaia/core] New issue created: #582",
    time: timeAgo(2),
  },
  {
    from: "Linear <notifications@linear.app>",
    subject: "You were mentioned in an issue",
    time: timeAgo(25),
  },
  {
    from: "Figma <noreply@figma.com>",
    subject: "Dhruv left a comment on 'Homepage V3'",
    time: timeAgo(28),
  },
];
const fetchData: EmailFetchData[] = Array.from({ length: 5 })
  .flatMap(() => initialFetchData)
  .map((email, index) => ({ ...email, thread_id: `thread_${index + 1}` }));

const summaryComponent = (
  <div className="rounded-xl border border-white/10 bg-slate-800/30 p-6 backdrop-blur-sm">
    <div className="mb-4 flex items-center gap-3">
      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-700">
        <Mail className="h-4 w-4 text-white" />
      </div>
      <h3 className="text-lg font-semibold text-white">Email Summary</h3>
    </div>
    <div className="space-y-3">
      <p className="text-sm text-gray-300">
        Here's a comprehensive analysis of the email from Product Hunt Daily...
      </p>
      <div className="space-y-2">
        <div className="rounded-lg border border-white/5 bg-slate-800/50 p-3">
          <h4 className="mb-1 text-sm font-medium text-gray-200">
            Core Message
          </h4>
          <p className="text-xs text-gray-400">
            Discusses challenges faced by founders and their journey to reapply
            to YC, featuring new workflow tools and startup stories.
          </p>
        </div>
        <div className="rounded-lg border border-white/5 bg-slate-800/50 p-3">
          <h4 className="mb-1 text-sm font-medium text-gray-200">
            Key Highlights
          </h4>
          <ul className="space-y-1 text-xs text-gray-400">
            <li>• Okibi: Workflow automation agent platform</li>
            <li>• Mocha: Full-stack app generator with deployment</li>
            <li>• GitBook: Dynamic adaptive documentation</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
);

const mockComposerValue = {
  appendToInput: (text: string) => {
    console.log(`EmailListCard tried to append: "${text}"`);
  },
};

// --- SELF-ANIMATING COMPONENTS FOR EACH STEP ---

const ComposeAnimation = () => (
  <motion.div
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.4, ease: "easeOut" }}
  >
    <EmailComposeSection email_compose_data={composeData} />
  </motion.div>
);

const FetchAnimation = () => {
  const [visibleEmails, setVisibleEmails] = useState<EmailFetchData[]>([]);
  const [isExpanded, setIsExpanded] = useState(false);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const expandTimer = setTimeout(() => setIsExpanded(true), 200);

    let emailTimers: NodeJS.Timeout[] = [];
    if (isExpanded) {
      emailTimers = fetchData.map((email, index) =>
        setTimeout(() => {
          setVisibleEmails((prev) => {
            const newEmails = [...prev, email];
            // Smooth scroll to bottom after adding email
            setTimeout(() => {
              if (scrollContainerRef.current) {
                scrollContainerRef.current.scrollTo({
                  top: scrollContainerRef.current.scrollHeight,
                  behavior: "smooth",
                });
              }
            }, 50);
            return newEmails;
          });
        }, index * 150),
      );
    }
    return () => {
      clearTimeout(expandTimer);
      emailTimers.forEach(clearTimeout);
    };
  }, [isExpanded]);

  return (
    <motion.div
      initial={{ opacity: 0, height: "60px" }}
      animate={{
        opacity: 1,
        height: isExpanded ? "350px" : "60px",
      }}
      transition={{ duration: 0.5, ease: "easeInOut" }}
      className="overflow-hidden"
    >
      <div ref={scrollContainerRef} className="h-full overflow-y-auto">
        <EmailListCard emails={visibleEmails} />
      </div>
    </motion.div>
  );
};

const ViewAnimation = () => {
  const [showSummary, setShowSummary] = useState(false);

  useEffect(() => {
    const summaryTimer = setTimeout(() => setShowSummary(true), 1000);

    return () => {
      clearTimeout(summaryTimer);
    };
  }, []);

  return (
    <div className="w-full space-y-4">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
      >
        <EmailThreadCard emailThreadData={threadData} />
      </motion.div>

      <AnimatePresence>
        {showSummary && (
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
          >
            {summaryComponent}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

// --- MAIN EXPORTED STEPS ---

export const animationSteps = [
  {
    name: "Compose",
    icon: <Send />,
    prompt:
      "Compose an email to dhruv@heygaia.io asking about the investor meeting.",
    component: <ComposeAnimation />,
  },
  {
    name: "Fetch",
    icon: <Mail />,
    prompt: "Fetch my latest emails from Gmail.",
    component: <FetchAnimation />,
  },
  {
    name: "View",
    icon: <Inbox />,
    prompt: "Tell me about the email from Product Hunt.",
    component: <ViewAnimation />,
  },
];
