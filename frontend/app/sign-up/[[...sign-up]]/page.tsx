import { SignUp } from "@clerk/nextjs"

export default function SignUpPage() {
  return (
    <main style={{ display: "flex", justifyContent: "center", paddingTop: 80 }}>
      <SignUp />
    </main>
  )
}
