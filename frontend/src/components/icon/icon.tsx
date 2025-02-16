import { cn } from "@/lib/utils";
import { icons } from "lucide-react";
import { HTMLAttributes } from "react";

export interface LucideIconProps extends HTMLAttributes<HTMLOrSVGElement> {
  name: keyof typeof icons;
  size?: number;
}

const LucideIcon = ({ name, size = 16, className, ...props }: LucideIconProps) => {
  const Icon = icons[name];

  if (!Icon) {
    console.warn(`Icon "${name}" not found`);
    return null;
  }

  const isClickEvent = !!props.onClick;
  const pointerStyle = isClickEvent ? "cursor-pointer" : "";

  return <Icon size={size} className={cn(pointerStyle, className)} {...props} />;
};

export default LucideIcon;
