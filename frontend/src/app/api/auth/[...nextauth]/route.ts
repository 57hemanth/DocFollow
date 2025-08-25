import NextAuth, { AuthOptions, User, Session, Account } from "next-auth"
import { JWT } from "next-auth/jwt"
import GoogleProvider from "next-auth/providers/google"
import CredentialsProvider from "next-auth/providers/credentials"
import clientPromise from "@/lib/mongodb"
import bcrypt from "bcrypt"

export const authOptions: AuthOptions = {
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID as string,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET as string,
    }),
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        email: { label: "Email", type: "text" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials) {
          return null
        }
        const db = (await clientPromise).db()
        const user = await db
          .collection("doctors")
          .findOne({ email: credentials.email })

        if (user && user.password) {
          const isValid = await bcrypt.compare(credentials.password, user.password)
          if (isValid) {
            return {
              id: user._id.toHexString(),
              name: user.name,
              email: user.email,
              image: user.image,
            }
          }
        }
        return null
      },
    }),
  ],
  pages: {
    signIn: "/login",
  },
  session: {
    strategy: "jwt",
  },
  callbacks: {
    async signIn({ user }) {
      if (!user.email || !user.name) {
        return false
      }

      const db = (await clientPromise).db()
      const existingDoctor = await db
        .collection("doctors")
        .findOne({ email: user.email })

      if (existingDoctor) {
        return true
      }

      const newDoctor = {
        name: user.name,
        email: user.email,
        image: user.image,
        createdAt: new Date(),
        updatedAt: new Date(),
        emailVerified: new Date(),
        whatsapp_connected: false,
        google_calendar_connected: false,
      }

      await db.collection("doctors").insertOne(newDoctor)
      return true
    },
    async jwt({
      token,
      user,
      account,
    }: {
      token: JWT
      user: User
      account: Account | null
    }) {
      if (account && user) {
        const db = (await clientPromise).db()
        const doctor = await db
          .collection("doctors")
          .findOne({ email: user.email })
        if (doctor) {
          token.id = doctor._id.toHexString()
        }
      }
      return token
    },
    async session({ session, token }: { session: Session; token: JWT }) {
      if (session.user) {
        session.user.id = token.id as string
      }
      return session
    },
  },
}

const handler = NextAuth(authOptions)

export { handler as GET, handler as POST }
