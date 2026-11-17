import { appendFile, readFile } from 'node:fs/promises';
import { resolve } from 'node:path';

type IncomingTeamsMessage = {
  activityId: string;
  senderName?: string;
  text: string;
  receivedAt: Date;
};

type OrganizerTask = {
  activityId: string;
  origem: 'Teams';
  assunto: string;
  descricao: string;
  data_recebimento: string;
  prazo: string;
  prioridade: 'Média';
  status: 'Pendente';
};

function isNodeError(error: unknown): error is NodeJS.ErrnoException {
  return error instanceof Error;
}

function dateInLocalTime(value: Date): string {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, '0');
  const day = String(value.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export class TeamsInboxStore {
  private readonly activityIds: Set<string>;
  private writeQueue: Promise<void> = Promise.resolve();

  private constructor(
    private readonly filePath: string,
    activityIds: Set<string>
  ) {
    this.activityIds = activityIds;
  }

  static async create(): Promise<TeamsInboxStore> {
    const configuredPath = process.env.ORGANIZER_INBOX_PATH;
    const filePath = resolve(
      configuredPath ?? resolve(process.cwd(), '..', 'teams_inbox.jsonl')
    );
    let contents: string;
    try {
      contents = await readFile(filePath, 'utf8');
    } catch (error: unknown) {
      if (isNodeError(error) && 'code' in error && error.code === 'ENOENT') {
        return new TeamsInboxStore(filePath, new Set());
      }
      throw error;
    }

    const activityIds = new Set<string>();
    for (const [index, line] of contents.split(/\r?\n/).entries()) {
      if (!line.trim()) {
        continue;
      }
      let item: unknown;
      try {
        item = JSON.parse(line);
      } catch (error: unknown) {
        throw new Error(`Mensagem inválida na linha ${index + 1} de ${filePath}.`, {
          cause: error,
        });
      }
      if (
        typeof item !== 'object' ||
        item === null ||
        !('activityId' in item) ||
        typeof item.activityId !== 'string'
      ) {
        throw new Error(`Identificador ausente na linha ${index + 1} de ${filePath}.`);
      }
      activityIds.add(item.activityId);
    }
    return new TeamsInboxStore(filePath, activityIds);
  }

  async saveMessage(message: IncomingTeamsMessage): Promise<boolean> {
    const save = this.writeQueue.then(async () => {
      if (this.activityIds.has(message.activityId)) {
        return false;
      }

      const receivedDate = dateInLocalTime(message.receivedAt);
      const task: OrganizerTask = {
        activityId: message.activityId,
        origem: 'Teams',
        assunto: `Mensagem de ${message.senderName || 'usuário do Teams'}`,
        descricao: message.text,
        data_recebimento: receivedDate,
        prazo: receivedDate,
        prioridade: 'Média',
        status: 'Pendente',
      };

      await appendFile(this.filePath, `${JSON.stringify(task)}\n`, {
        encoding: 'utf8',
        flag: 'a',
      });
      this.activityIds.add(message.activityId);
      return true;
    });
    this.writeQueue = save.then(
      () => undefined,
      () => undefined
    );
    return save;
  }
}
