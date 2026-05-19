import { apiRequest } from "./api"; 

export const KnowlegeMapAPI = {

  async getAll() {
    return apiRequest('knowlege_map.php', {
      action: 'getall'
    })
  },

  async updatePosition(id: string, position: { x: number, y: number }) {
    return apiRequest('knowlege_map.php', {
      action: 'updateposition',
      id,
      position
    })
  },

  async createRelation(relation: { source: string, target: string }) {
    return apiRequest('knowlege_map.php', {
      action: 'createrelation',
      ...relation
    })
  },

  async deleteRelation(id: string) {
    return apiRequest('knowlege_map.php', {
      action: 'deleterelation',
      id
    })
  }


}