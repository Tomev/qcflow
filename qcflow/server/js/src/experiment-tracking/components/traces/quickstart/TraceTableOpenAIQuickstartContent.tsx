import { CopyIcon, Typography, useDesignSystemTheme } from '@databricks/design-system';
import { FormattedMessage } from 'react-intl';
import { CodeSnippet } from '@databricks/web-shared/snippet';
import { CopyButton } from '@qcflow/qcflow/src/shared/building_blocks/CopyButton';

export const TraceTableOpenAIQuickstartContent = ({
  baseComponentId,
  experimentId,
  runUuid,
}: {
  baseComponentId: string;
  experimentId: string | null;
  runUuid?: string;
}) => {
  const { theme } = useDesignSystemTheme();
  const code = `import qcflow
from openai import OpenAI
${experimentId ? `\nqcflow.set_experiment(experiment_id="${experimentId}")` : ''}
qcflow.openai.autolog()

# Ensure that the "OPENAI_API_KEY" environment variable is set
client = OpenAI()

messages = [
  {"role": "system", "content": "You are a helpful assistant."},
  {"role": "user", "content": "Hello!"}
]

# Inputs and outputs of the API request will be logged in a trace
${
  runUuid ? `with qcflow.start_run():\n    ` : ''
}client.chat.completions.create(model="gpt-4o-mini", messages=messages)`;

  return (
    <div>
      <Typography.Text>
        <FormattedMessage
          defaultMessage="Automatically log traces for OpenAI API calls by calling the {code} function. For example:"
          description="Description of how to log traces for the OpenAI package using QCFlow autologging. This message is followed by a code example."
          values={{
            code: <code>qcflow.openai.autolog()</code>,
          }}
        />
      </Typography.Text>
      <div css={{ position: 'relative', width: 'min-content' }}>
        <CopyButton
          componentId={`${baseComponentId}.traces_table.openai_quickstart_snippet_copy`}
          css={{ zIndex: 1, position: 'absolute', top: theme.spacing.xs, right: theme.spacing.xs }}
          showLabel={false}
          copyText={code}
          icon={<CopyIcon />}
        />
        <CodeSnippet
          showLineNumbers
          style={{
            padding: `${theme.spacing.sm}px ${theme.spacing.md}px`,
            marginTop: theme.spacing.md,
          }}
          language="python"
        >
          {code}
        </CodeSnippet>
      </div>
    </div>
  );
};
