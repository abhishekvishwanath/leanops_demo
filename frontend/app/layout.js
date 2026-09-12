import "./globals.css";
import Nav from "../components/Nav";

export const metadata = {
  title: "XYZ Properties — Dealer Dashboard",
  description: "AI lead-conversion demo dealer dashboard",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <div className="flex min-h-screen">
          <Nav />
          <main className="flex-1 p-6 max-w-[1400px]">{children}</main>
        </div>
      </body>
    </html>
  );
}
