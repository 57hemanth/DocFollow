import { redirect } from "next/navigation"

export default function Page() {
  redirect("/dashboard/patients")
  return null
}
