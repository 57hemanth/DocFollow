"use client"
import * as React from "react"
import { Stethoscope, LogOut } from "lucide-react"
import { usePathname } from "next/navigation"
import { signOut } from "next-auth/react"
import { useSession } from "next-auth/react"

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
} from "@/components/ui/sidebar"
import Link from "next/link"

// This is sample data.
const data = {
  navMain: [
    {
      title: "Patients",
      url: "/dashboard/patients",
    },
    {
      title: "Follow Ups",
      url: "/dashboard/follow-ups",
    },
    {
      title: "Appointments",
      url: "/dashboard/appointments",
    },
    {
      title: "Settings",
      url: "/dashboard/settings",
    },
  ],
}

export function AppSidebar() {
  const { data: session } = useSession()
  const pathname = usePathname()
  return (
    <Sidebar variant="floating">
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" asChild>
              <a href="#">
                <div className="bg-sidebar-primary text-sidebar-primary-foreground flex aspect-square size-8 items-center justify-center rounded-lg">
                  {session?.user?.image ? (
                    <img
                      src={session.user.image}
                      alt={session.user.name ?? "user-image"}
                      className="size-8 rounded-lg"
                    />
                  ) : (
                    <Stethoscope className="size-4" />
                  )}
                </div>
                <div className="flex flex-col">
                  {/* <span className="text-xs text-slate-500">Welcome back,</span> */}
                  <span className="font-medium text-sm md:text-base lg:text-base">{session?.user?.name}</span>
                </div>
              </a>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarMenu className="gap-2">
            {data.navMain.map((item) => (
              <SidebarMenuItem key={item.title}>
                <SidebarMenuButton asChild isActive={pathname === item.url}>
                  <Link href={item.url} className="font-light text-sm md:text-base lg:text-base">
                    {item.title}
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
            ))}
          </SidebarMenu>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton className="cursor-pointer text-sm md:text-base lg:text-base" onClick={() => signOut()}>
              <LogOut className="size-4" />
              Logout
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  )
}
