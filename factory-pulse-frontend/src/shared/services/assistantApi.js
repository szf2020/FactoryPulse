import axios from 'axios';

/**
 * Axios instance for the FactoryPulse Assistant service.
 * Separate from `api` (the Django REST backend) because the assistant is its
 * own microservice with its own base URL and no JWT requirement — `/ask` is
 * answered using the assistant's own read-only FactoryPulse credentials.
 */
const assistantApi = axios.create({
  baseURL: 'http://127.0.0.1:8001/',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    accept: 'application/json',
  },
});

/**
 * Asks the FactoryPulse Assistant a natural-language question.
 * @param {string} question
 * @returns {Promise<string>} the assistant's answer
 */
export const askAssistant = async (question) => {
  const response = await assistantApi.post('ask', { question });
  return response.data.answer;
};

export default assistantApi;
