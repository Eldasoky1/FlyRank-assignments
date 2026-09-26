import { test, expect } from '@playwright/test'

test('primary flow: user asks a question, assistant streams an answer', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByLabel('Message the assistant')).toBeVisible()
  await page.getByLabel('Message the assistant').fill('What is the capstone plan?')
  await page.getByRole('button', { name: 'Send' }).click()

  await expect(page.getByTestId('bubble-user')).toContainText('capstone plan')
  // Streaming answer eventually completes and lands as an assistant bubble.
  await expect(page.getByTestId('bubble-assistant')).toContainText(/streamed reply/, { timeout: 20000 })
})

test('error path: a mid-stream failure renders the designed error with retry', async ({ page }) => {
  await page.addInitScript(() => {
    window.__SABOTAGE = ['mid-stream']
  })
  await page.goto('/')
  await page.getByLabel('Message the assistant').fill('stream to me')
  await page.getByRole('button', { name: 'Send' }).click()

  const alert = page.getByRole('alert')
  await expect(alert).toContainText(/Connection lost mid-stream/, { timeout: 20000 })
  await expect(alert.getByRole('button', { name: 'Retry' })).toBeVisible()
})

test('empty state guides the user before any message', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByText(/No conversations yet/)).toBeVisible()
})