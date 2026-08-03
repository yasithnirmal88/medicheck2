/**
 * Reusable question-type input components.
 *
 * Every component follows the shared `QuestionInputProps<T>` shape (see ./types).
 * The canonical domain names exported below are the friendly aliases the
 * QuestionRenderer maps a `question_type` to. Original component names are
 * re-exported too for consumers that prefer explicit imports.
 *
 * Do not build answer-handling logic here — these are pure UI inputs.
 */

import SingleChoice from './SingleChoice'
import MultipleChoice from './MultipleChoice'
import YesNo from './YesNo'
import DropdownInput from './DropdownInput'
import SliderInput from './SliderInput'
import DateInput from './DateInput'
import TimeInput from './TimeInput'
import NumericInput from './NumericInput'
import DecimalInput from './DecimalInput'
import FreeTextInput from './FreeTextInput'
import MultiSelectInput from './MultiSelectInput'
import SearchInput from './SearchInput'
import FileUploadInput from './FileUploadInput'

export type { QuestionInputProps, QuestionInputComponent } from './types'

// Friendly domain aliases (no name collisions with the originals).
export const RadioInput = SingleChoice
export const CheckboxInput = MultipleChoice
export const YesNoInput = YesNo
export const Dropdown = DropdownInput
export const Slider = SliderInput
export const DatePicker = DateInput
export const TimePicker = TimeInput
export const NumberInput = NumericInput
export const TextArea = FreeTextInput
export const MultiSelect = MultiSelectInput
export const Search = SearchInput
export const FileUpload = FileUploadInput

// Original component names for explicit consumers.
export {
  SingleChoice,
  MultipleChoice,
  YesNo,
  DropdownInput,
  SliderInput,
  DateInput,
  TimeInput,
  NumericInput,
  DecimalInput,
  FreeTextInput,
  MultiSelectInput,
  SearchInput,
  FileUploadInput,
}
