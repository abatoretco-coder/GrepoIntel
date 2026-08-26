"use client"

import * as React from "react"
import { Dialog } from "radix-ui"
import { X } from "lucide-react"
import { cn } from "@/lib/utils"

const Sheet = Dialog.Root
const SheetTrigger = Dialog.Trigger
const SheetClose = Dialog.Close

function SheetContent({className, children, ...props}: React.ComponentProps<typeof Dialog.Content>) {
  return <Dialog.Portal><Dialog.Overlay className="sheet-overlay"/><Dialog.Content className={cn("sheet-content", className)} {...props}>{children}<Dialog.Close className="sheet-close" aria-label="Fermer"><X size={18}/></Dialog.Close></Dialog.Content></Dialog.Portal>
}
function SheetHeader({className, ...props}: React.ComponentProps<"div">) { return <div className={cn("sheet-header",className)} {...props}/> }
function SheetTitle({className, ...props}: React.ComponentProps<typeof Dialog.Title>) { return <Dialog.Title className={cn("sheet-title",className)} {...props}/> }
function SheetDescription({className, ...props}: React.ComponentProps<typeof Dialog.Description>) { return <Dialog.Description className={cn("sheet-description",className)} {...props}/> }

export {Sheet,SheetTrigger,SheetClose,SheetContent,SheetHeader,SheetTitle,SheetDescription}
