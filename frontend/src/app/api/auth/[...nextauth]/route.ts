import NextAuth, { AuthOptions } from "next-auth"
import GoogleProvider from "next-auth/providers/google"
import clientPromise from "@/lib/mongodb"

export const authOptions: AuthOptions = {
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID as string,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET as string,
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
    async jwt({ token, user }: { token: any; user: any }) {
      if (user) {
        // On initial sign-in, add the user's ID to the token
        const db = (await clientPromise).db()
        const dbUser = await db
          .collection("doctors")
          .findOne({ email: user.email as string })
        if (dbUser) {
          token.id = dbUser._id.toHexString()
        }
      }
      return token
    },
    async session({ session, token }: { session: any; token: any }) {
      if (session.user) {
        session.user.id = token.id as string
      }
      return session
    },
  },
}

const handler = NextAuth(authOptions)

export { handler as GET, handler as POST }
