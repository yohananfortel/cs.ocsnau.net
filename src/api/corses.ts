import { apiRequest } from "./api"; 

export const CorsesAPI = {

  async getAll() {
    return apiRequest('corses.php', {
      action: 'getall'
    })
  },

  async getOne(id: number | string) {
    return apiRequest('corses.php', {
      action: 'view',
      id
    })
  },

  async add(topic: string) {
    return apiRequest('corses.php', {
      action: 'add',
      topic
    })
  }

  /** 
  async upateOrder(orderData: { id: number | string, topic: string, order: number }[]) {
    return apiRequest('corses.php', {
      action: 'update_order',
      id,
      topic,
      order
    })
  }*/

}   