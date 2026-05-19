const API_URL = 'https://cs.ocsnau.net/nxrfzzjm_server'

export async function apiRequest(
  endpoint: string,
  body: any = {}
) {
  const response = await fetch(`${API_URL}/${endpoint}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(body)
  })

  if (!response.ok) {
    console.error('API request error:', response.text())  
    throw new Error('Помилка мережі')
    
  }

  return response.json()
}