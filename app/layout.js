import './globals.css'
import { Providers } from './providers'

export const metadata = {
  title: 'PHD - Psychological Health Detector',
  description: 'Deteksi & asesmen kesehatan mental otomatis keluarga: SDQ, GHQ-12, PHQ-9 dengan skoring & rekomendasi otomatis.',
}

export default function RootLayout({ children }) {
  return (
    <html lang="id">
      <head>
        <script dangerouslySetInnerHTML={{__html:'window.addEventListener("error",function(e){if(e.error instanceof DOMException&&e.error.name==="DataCloneError"&&e.message&&e.message.includes("PerformanceServerTiming")){e.stopImmediatePropagation();e.preventDefault()}},true);'}} />
      </head>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
