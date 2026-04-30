import { SignIn } from "@clerk/nextjs"

export default function SignInPage() {
  return (
    <main style={{ display: "flex", justifyContent: "center", paddingTop: 80 }}>
      <SignIn />
    </main>
  )
}
