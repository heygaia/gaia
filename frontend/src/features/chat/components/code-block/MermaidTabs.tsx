import { Tab, Tabs } from "@heroui/tabs";
import React from "react";

import FlowchartPreview from "./FlowchartPreview";
import MermaidCode from "./MermaidCode";

interface SyntaxHighlighterProps {
  language?: string;
  style?: { [key: string]: unknown };
  customStyle?: { [key: string]: unknown };
  className?: string;
  showLineNumbers?: boolean;
  startingLineNumber?: number;
  wrapLines?: boolean;
  lineProps?: { [key: string]: unknown };
}

interface MermaidTabsProps {
  children: React.ReactNode;
  activeTab: string;
  onTabChange: (key: string) => void;
  isLoading: boolean;
  syntaxHighlighterProps?: SyntaxHighlighterProps;
}

const MermaidTabs: React.FC<MermaidTabsProps> = ({
  children,
  activeTab,
  onTabChange,
  isLoading,
  syntaxHighlighterProps,
}) => {
  return (
    <Tabs
      className="px-3"
      disabledKeys={isLoading ? ["editor"] : []}
      selectedKey={activeTab}
      variant="underlined"
      onSelectionChange={(key) => onTabChange(key as string)}
    >
      <Tab key="preview" className="p-0" title="Flowchart">
        <FlowchartPreview>{children}</FlowchartPreview>
      </Tab>
      <Tab key="code" title="Code">
        <MermaidCode syntaxHighlighterProps={syntaxHighlighterProps}>
          {children}
        </MermaidCode>
      </Tab>
    </Tabs>
  );
};

export default MermaidTabs;
