import { apiRequest } from './api'


interface UpdateActionData {
  content?: string;
  title?: string;
  type?: string | number;
  slug?: string;
}


export const ActionsAPI = {

  async getAll(slug: string | number) {
    return apiRequest('actions.php', {
      action: 'getall',
      slug
    })
  },

  async getOne(id: number | string) {
    return apiRequest('actions.php', {
      action: 'view',
      id
    })
  },

  async add(slug: string | number, topic: string, type: number | string | null) {
    return apiRequest('actions.php', {
      action: 'add',
      slug,
      topic,
      type
    })
  },

  async getTypes() {
    return apiRequest('actions.php', {
      action: 'get_types_actions'
    })
  },

  async update(id: number | string, data: Partial<UpdateActionData>) {
    return apiRequest('actions.php', {
      action: 'update',
      id,
      ...data
    })
  },

  async delete(id: number | string) {
    return apiRequest('actions.php', {
      action: 'delete',
      id
    })
  },

  async updateOrder(courseId: number | string, orderedIds: (number | string)[]) {
    return apiRequest('actions.php', {
      action: 'update_order',
      course_id: courseId,
      ordered_ids: orderedIds
    })
  }
}

/*
slug: props.slug,
      topic: topic.value,
      type: type.value
*/