import { App } from '@microsoft/teams.apps';
import { TeamsInboxStore } from './inbox-store.js';

async function main() {
  const app = new App();
  const inboxStore = await TeamsInboxStore.create();

  app.on('message', async ({ activity, reply }) => {
    const text = activity.text.trim();
    if (!text) {
      await reply('Envie uma mensagem de texto para eu cadastrar no organizador.');
      return;
    }

    const saved = await inboxStore.saveMessage({
      activityId: activity.id,
      senderName: activity.from.name,
      text,
      receivedAt: activity.localTimestamp ?? activity.timestamp ?? new Date(),
    });

    await reply(
      saved
        ? 'Mensagem registrada como tarefa pendente. No organizador, clique em "Atualizar Teams" para vê-la.'
        : 'Essa mensagem já tinha sido registrada no organizador.'
    );
  });

  await app.start(process.env.PORT || 3978);
}

main().catch((error: unknown) => {
  console.error('Não foi possível iniciar o agente do Teams:', error);
  process.exitCode = 1;
});
