import clientPromise from "@/lib/mongodb"
import { NextResponse } from "next/server"
import bcrypt from "bcrypt"

export async function POST(request: Request) {
  const { name, email, password } = await request.json()

  if (!name || !email || !password) {
    return NextResponse.json(
      { message: "Missing required fields" },
      { status: 400 }
    )
  }

  const hashedPassword = await bcrypt.hash(password, 10)
  const db = (await clientPromise).db()

  const existingDoctor = await db.collection("doctors").findOne({ email })

  if (existingDoctor) {
    return NextResponse.json(
      { message: "User with this email already exists" },
      { status: 409 }
    )
  }

  const newDoctor = {
    name,
    email,
    password: hashedPassword,
    createdAt: new Date(),
    updatedAt: new Date(),
    whatsapp_connected: false,
    google_calendar_connected: false,
  }

  await db.collection("doctors").insertOne(newDoctor)

  return NextResponse.json(
    { message: "User created successfully" },
    { status: 201 }
  )
}
