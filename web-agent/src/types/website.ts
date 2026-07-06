export type WebsiteInfo = {
  url: string
  title: string
  domain: string
  protocol: string
  favicon: string
  https: boolean
  connectionType: string
  ipAddress: string
  country: string
  lastScan: string
  pageText?: string
  forms?: number
  scripts?: number
  passwordFields?: number
  iframes?: number
}
