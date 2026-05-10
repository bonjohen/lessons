export interface Deployment {
  id: string;
  name: string;
  description: string;
  siteUrl: string;
  apiUrl: string;
  workflowFile: string | null;
  profile: string;
}

const GITHUB_REPO = 'bonjohen/lessons';

export const DEPLOYMENTS: Deployment[] = [
  {
    id: 'local',
    name: 'Local',
    description: 'Development server with Ollama + ChromaDB',
    siteUrl: 'http://localhost:4321/lessons/',
    apiUrl: 'http://localhost:8000',
    workflowFile: null,
    profile: 'local',
  },
  {
    id: 'github-pages',
    name: 'GitHub Pages',
    description: 'Static site only — no backend',
    siteUrl: 'https://bonjohen.github.io/lessons/',
    apiUrl: '',
    workflowFile: 'build-deploy.yml',
    profile: 'local',
  },
  {
    id: 'flyio',
    name: 'Fly.io',
    description: 'OpenAI + ChromaDB on persistent volume',
    siteUrl: '',
    apiUrl: '',
    workflowFile: 'deploy-flyio.yml',
    profile: 'flyio',
  },
  {
    id: 'railway',
    name: 'Railway',
    description: 'OpenAI + ChromaDB on persistent volume',
    siteUrl: '',
    apiUrl: '',
    workflowFile: 'deploy-railway.yml',
    profile: 'railway',
  },
  {
    id: 'aws',
    name: 'AWS',
    description: 'Bedrock + OpenSearch on ECS Fargate',
    siteUrl: '',
    apiUrl: '',
    workflowFile: 'deploy-aws.yml',
    profile: 'aws',
  },
  {
    id: 'azure',
    name: 'Azure',
    description: 'Azure OpenAI + AI Search on Container Apps',
    siteUrl: '',
    apiUrl: '',
    workflowFile: 'deploy-azure.yml',
    profile: 'azure',
  },
  {
    id: 'gcp',
    name: 'GCP',
    description: 'Vertex AI + Vector Search on Cloud Run',
    siteUrl: '',
    apiUrl: '',
    workflowFile: 'deploy-gcp.yml',
    profile: 'gcp',
  },
];

export function workflowUrl(workflowFile: string): string {
  return `https://github.com/${GITHUB_REPO}/actions/workflows/${workflowFile}`;
}
